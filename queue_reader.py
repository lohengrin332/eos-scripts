#!/usr/bin/python -u

from collections import OrderedDict
from json import dumps, load, loads
import os
import pika
from random import randint
import signal
import threading
import time
import unicornhathd as uhhd

# uhhd.brightness(1)
# uhhd.set_pixel(0, 0, 150, 150, 0)
# uhhd.show()
#
# time.sleep(1)
#
# uhhd.off()

use_animation = True

script_path = os.path.dirname(os.path.abspath(__file__))

with open('{sp}/test_interfaces.config.json'.format(sp=script_path), 'r') as f:
    config = load(f)

running = True
def graceful_exit(*args):
    global running
    global rabbit
    print('Exiting gracefully...')
    running = False
    rabbit.stop_receiving()

class Pixel:
    cycle_count = 54
    target_rgb = [0, 0, 0]
    current_rgb = [0, 0, 0]
    increment = [0, 0, 0]
    animate = False

    def __init__(
        self,
        is_edge=False,
        is_successful=True,
        is_blank=False,
        source=0,
        animate=False,
    ):
        if is_blank:
            self.current_rgb = self.target_rgb = [0, 0, 0]
            self.animate = False
        elif not is_successful:
            self.current_rgb = self.target_rgb = [255, 0, 0]
            self.animate = False
        else:
            self.animate = animate

            if is_edge:
                color = randint(54, 70)
                marker_color = 0
            else:
                color = randint(114, 140)
                marker_color = color

            red = color
            green = color
            blue = color

            if source == 0:
                green = marker_color
            elif source == 1:
                blue = marker_color
            else:
                red = marker_color

            self.target_rgb = [red, green, blue]

            zeros = [0, 0, 0]
            if self.animate:
                self.current_rgb = zeros
                self.increment = [
                    max(round(red / self.cycle_count), 1),
                    max(round(green / self.cycle_count), 1),
                    max(round(blue / self.cycle_count), 1),
                ]
            else:
                self.current_rgb = self.target_rgb
                self.increment = zeros

    @staticmethod
    def EMPTY_PIXEL():
        return Pixel(is_blank=True)

    def increment_animation(self):
        # print(
        #     'incrementing pixel'
        #     f'r/g/b ({self.current_rgb[0]}/{self.current_rgb[1]}/{self.current_rgb[2]}), '
        #     f't r/g/b ({self.target_rgb[0]}/{self.target_rgb[1]}/{self.target_rgb[2]})'
        # )
        for p in range(3):
            self.current_rgb[p] += (
                self.increment[p] if self.current_rgb[p] < self.target_rgb[p] else 0
            )

    def get_rgb(self):
        if self.animate:
            if sum(self.target_rgb) > sum(self.current_rgb):
                self.increment_animation()
            else:
                self.animate = False

        return self.current_rgb

    def get_is_animating(self):
        return self.animate


class RabbitConn:
    consumer_tag = None

    def __init__(self, rabbit_config):
        credentials = pika.PlainCredentials(rabbit_config['user'], rabbit_config['password'])
        parameters = pika.ConnectionParameters(host=rabbit_config['host'], credentials=credentials)
        self.queue = rabbit_config['queue']
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True, arguments={
            'x-max-length': rabbit_config['max-queue-length']
        })

    def send(self, results):
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=dumps(results))

    def receive(self, callback):
        self.consumer_tag = self.channel.basic_consume(queue=self.queue, auto_ack=True, on_message_callback=callback)
        self.channel.start_consuming()

    def stop_receiving(self):
        self.channel.basic_cancel(self.consumer_tag)

    def disconnect(self):
        self.connection.close()


class ResultsGrid:
    def __init__(self, config):
        self.max_length = 16
        self.row_length = 4
        self.use_markers = False
        self.config = config
        self.queues = OrderedDict()
        self.interface_to_pos = {}
        self.target_to_pos = {}
        self.clear_grid()
        self._init_interface_to_pos()
        self._init_target_to_pos()

    def clear_grid(self):
        for connection in self.config['connection_configs']:
            interface = connection['interface']
            self.queues[interface] = self._gen_empty_queue()
        self.queues['local'] = self._gen_empty_queue()
        self.queues['combined'] = self._gen_empty_queue()

    def _init_interface_to_pos(self):
        count = 0
        for interface in self.queues:
            self.interface_to_pos[interface] = count
            count += 1

    def _init_target_to_pos(self):
        count = -1
        for target in self.config['ips_to_ping']:
            count += 1
            self.target_to_pos[target] = count

        for target in self.config['hosts_to_ping']:
            # Intentionally not incrementing count here so the hosts can be last, regardless of host is being pinged.
            self.target_to_pos[target] = count

    def _gen_empty_queue(self):
        queue = []
        for x in range(self.max_length):
            queue.append(self._gen_empty_row())
        return queue

    def _gen_empty_row(self):
        row = []
        for x in range(self.row_length):
            row.append({
                'pixel': Pixel.EMPTY_PIXEL(),
                'result': False
            })
        return row

    def _gen_pixel(self, source, result):
        is_edge = result['target'] in self.config['hosts_to_ping']
        is_successful = result['result']

        return Pixel(
            is_edge = is_edge,
            is_successful = is_successful,
            source = source,
            animate = use_animation,
        )

        # if not is_successful:
        #     pixel = Pixel(255, 0, 0, False)
        # else:
        #     if is_edge:
        #         color = randint(54, 70)
        #         marker_color = 0 if (
        #             is_marker or not self.use_markers
        #         ) else color
        #     else:
        #         color = randint(114, 140)
        #         marker_color = 0 if is_marker else color

        #     if source == 0:
        #         pixel = Pixel(color, marker_color, color, use_animation)
        #     elif source == 1:
        #         pixel = Pixel(color, color, marker_color, use_animation)
        #     else:
        #         pixel = Pixel(marker_color, color, color, use_animation)

        # return pixel

    def add_message(self, message):
        if message['interface'] not in self.queues:
            print('Found invalid interface (%s)' % (message['interface']))
        else:
            queue = self.queues[message['interface']]
            if message['target'] not in self.target_to_pos:
                print('Skipping unexpected target (%s) for interface (%s)'
                      % (message['target'], message['interface']))
                return
            target_position = self.target_to_pos[message['target']]

            if target_position == 0:
                queue.insert(0, self._gen_empty_row())
                self.trim_queue(queue)

            results = queue[0]
            results[target_position] = {
                'pixel': self._gen_pixel(self.interface_to_pos[message['interface']], message),
                'result': message['result']
            }

            # if target_position == len(results) - 1:
            #     queue.insert(0, self._gen_empty_row())
            #     self.trim_queue(queue)

    def trim_queue(self, queue):
        self.queues['combined'].insert(0, queue.pop())
        self.queues['combined'].pop()

    def for_display(self):
        _grid = []
        for x in range(self.max_length):
            row = []
            for interface in self.queues:
                queue = self.queues[interface]
                for y in range(self.row_length):
                    row.append(queue[x][y]['pixel'])
            _grid.append(row)
        return _grid


class ThreadedDraw(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global results_grid
        animating = True
        while animating:
            animating = set_uhhd(results_grid.for_display())


def set_uhhd(grid):
    animating = False
    for x in range(len(grid)):
        row = grid[x]
        for y in range(len(row)):
            # print(f'set_pixel({x}, {y}, [{row[y][0]}, {row[y][1]}, {row[y][2]}])')
            rgb = row[y].get_rgb()
            animating = animating or row[y].get_is_animating()
            uhhd.set_pixel(x, y, rgb[0], rgb[1], rgb[2])
    uhhd.show()
    return animating

messages_processed = 0
uhhd_thread = None

def msg_received(ch, method, properties, body):
    global results_grid
    global messages_processed
    global uhhd_thread
    messages_processed += 1
    # print(' [x] Received # %06d: %r' % (messages_processed, body))
    results = loads(body)
    print(' [x] Received # %06d: %11s/%s' % (messages_processed, results['service_name'], results['target']))
    results_grid.add_message(results)
    if uhhd_thread is None or not uhhd_thread.is_alive():
        uhhd_thread = ThreadedDraw()
        uhhd_thread.start()


signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

rabbit = RabbitConn(config['rabbit_config'])

results_grid = ResultsGrid(config)

uhhd.brightness(0.6)
uhhd.rotation(180)
set_uhhd(results_grid.for_display())

while running:
    try:
        rabbit.receive(msg_received)
    except KeyboardInterrupt:
        graceful_exit()

uhhd.off()
# for row in grid:
#     for col in row:
#         print('%r' % col)
#     print()
