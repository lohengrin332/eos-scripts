#!/usr/bin/env python

from collections import OrderedDict
from json import dumps, load, loads
import os
import pika
from random import randint
import signal
import unicornhathd as uhhd

# uhhd.brightness(1)
# uhhd.set_pixel(0, 0, 150, 150, 0)
# uhhd.show()
#
# time.sleep(1)
#
# uhhd.off()

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
        self.marker_frequency = 60
        self.config = config
        self.queues = OrderedDict()
        self.interface_to_pos = {}
        self.clear_grid()
        self._init_interface_to_pos()

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

    def _gen_empty_queue(self):
        queue = []
        for x in range(self.max_length):
            queue.append(self._gen_empty_row())
        return queue

    def _gen_empty_row(self):
        row = []
        for x in range(self.row_length):
            row.append({
                'pixel': self._gen_empty_pixel(),
                'result': False
            })
        return row

    def _gen_empty_pixel(self):
        return [0, 0, 0]

    def _gen_pixel(self, source, result):
        is_marker = randint(0, self.marker_frequency) == 0
        is_edge = result['target'] == 'yahoo.com'
        is_successful = result['result']

        if not is_successful:
            pixel = [255, 0, 0]
        else:
            if is_marker:
                pixel = [127, 127, 127]
            else:
                color = randint(58, 68) if is_edge else randint(119, 136)

                if source == 0:
                    pixel = [color, 0, color]
                elif source == 1:
                    pixel = [color, color, 0]
                else:
                    pixel = [0, color, color]

        return pixel

    def add_message(self, message):
        if message['interface'] not in self.queues:
            print('Found invalid message type (%s)'.format(message['interface']))
        else:
            queue = self.queues[message['interface']]
            results = []
            for result in message['results']:
                results.append({
                    'pixel': self._gen_pixel(self.interface_to_pos[message['interface']], result),
                    'result': result['result']
                })
            queue.insert(0, results)
            self.trim_queue(queue)

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


messages_processed = 0
def msg_received(ch, method, properties, body):
    global results_grid
    global messages_processed
    messages_processed += 1
    # print(' [x] Received # %06d: %r' % (messages_processed, body))
    print(' [x] Received # %06d' % messages_processed)
    results = loads(body)
    results_grid.add_message(results)
    set_uhhd(results_grid.for_display())

def set_uhhd(grid):
    for x in range(len(grid)):
        row = grid[x]
        for y in range(len(row)):
            # print(f'set_pixel({x}, {y}, [{row[y][0]}, {row[y][1]}, {row[y][2]}])')
            uhhd.set_pixel(x, y, row[y][0], row[y][1], row[y][2])
    uhhd.show()


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
