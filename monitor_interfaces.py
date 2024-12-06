#!/usr/bin/python -u
import argparse
from datetime import datetime
import threading
from json import load, dumps
from os import devnull, path
import pika
import signal
from subprocess import call, check_output, STDOUT
from time import sleep

script_path = path.dirname(path.abspath(__file__))

with open('{sp}/test_interfaces.config.json'.format(sp=script_path), 'r') as f:
    config = load(f)

DEVNULL = open(devnull, 'w')

class Connection:
    ip = None

    def __init__(self, interface, service_name):
        self.interface = interface
        self.service_name = service_name
        self.ping_count = 0

    def get_ip(self):
        if self.ip is None:
            self.ip = check_output(['{sp}/get_ip.sh'.format(sp=script_path), self.interface]).rstrip("\n")
            if self.ip == '':
                self.ip = 'INVALID IFACE'
        return self.ip

    def get_interface(self):
        return self.interface

    def get_service_name(self):
        return self.service_name

    def ping(self, ip, count=3):
        result = call([
            'sudo', 'ping', '-c', str(count), '-I', self.interface, ip,
        ], stdout=DEVNULL, stderr=STDOUT)

        return result == 0

    def ping_all(self, rabbit):
        global sig_handler
        self.ping_count += 1
        for ip in config['ips_to_ping']:
            result = {
                'interface': self.get_interface(),
                'service_name': self.get_service_name(),
                'target': ip,
                'result': self.ping(ip)
            }
            rabbit.send(result)
            if sig_handler.kill_now:
                break


class SigHandler:
    kill_now = False
    init_rabbit_reconnect = False
    reconnecting = False
    with_reconnect = False

    def __init__(self, with_reconnect=False):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.with_reconnect = with_reconnect

    def exit_gracefully(self, *args):
        print('{0} Exiting gracefully...'.format(datetime.now().isoformat()))
        self.kill_now = True

    def reconnect_rabbit(self, *args):
        print('{0} Requesting reconnect...'.format(datetime.now().isoformat()))
        if not self.with_reconnect:
            print('Reconnect disabled. Exiting.')
            self.exit_gracefully(*args)
        if len(args) > 0 and not self.kill_now:
            print('Underlying error:')
            print(args[0])
        if self.kill_now:
            print('Exiting in progress, will not request reconnect')
            self.init_rabbit_reconnect = False
        else:
            self.init_rabbit_reconnect = True


class RabbitConn:
    consumer_tag = None

    def __init__(self, rabbit_config):
        self.queue = rabbit_config['queue']
        self.rabbit_config = rabbit_config
        self.open_connection()

    def reconnect_if_needed(self):
        global sig_handler
        if not sig_handler.kill_now:
            if sig_handler.init_rabbit_reconnect:
                if not sig_handler.reconnecting:
                    sig_handler.reconnecting = True
                    self.disconnect()
                    try:
                        self.open_connection()
                    except Exception as e:
                        print('{0} Reconnect exception: {1}'.format(datetime.now().isoformat(), e))
                    sig_handler.init_rabbit_reconnect = False
                    sig_handler.reconnecting = False
                else:
                    print(
                        '{0} Reconnect in progress, skipping additional reconnect...'
                        .format(datetime.now().isoformat())
                    )
        else:
            print('{0} Reconnect requested, but exiting. Will not reconnect...'.format(datetime.now().isoformat()))

    def open_connection(self):
        credentials = pika.PlainCredentials(self.rabbit_config['user'], self.rabbit_config['password'])
        parameters = pika.ConnectionParameters(host=self.rabbit_config['host'], credentials=credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True, arguments={
            'x-max-length': self.rabbit_config['max-queue-length']
        })

    def send(self, results):
        global sig_handler
        if sig_handler.kill_now:
            return
        try:
            self.channel.basic_publish(exchange='', routing_key=self.queue, body=dumps(results))
        except (
            pika.exceptions.ChannelWrongStateError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ConnectionClosedByBroker,
        ) as err:
            sig_handler.reconnect_rabbit(err)
        except AssertionError as ae:
            if not sig_handler.kill_now:
                sig_handler.exit_gracefully()
            # print("AssertionError usually means a graceful_exit is in progress from another thread.\n%r" % ae)
        except Exception as e:
            if not sig_handler.kill_now:
                print('{0} Unexpected error, exiting...'.format(datetime.now().isoformat()))
                sig_handler.exit_gracefully()
                raise e

    def receive(self, callback):
        self.consumer_tag = self.channel.basic_consume(queue=self.queue, auto_ack=True, on_message_callback=callback)
        self.channel.start_consuming()

    def stop_receiving(self):
        self.channel.basic_cancel(self.consumer_tag)

    def disconnect(self):
        try:
            self.connection.close()
        except pika.exceptions.ConnectionWrongStateError as e:
            pass


def output(results):
    print(dumps(results))

def check(connections, rabbit):
    results = []
    for connection in connections:
        results.append({
            'service_name': connection.get_service_name(),
            'interface': connection.get_interface(),
            'results': connection.ping_all(rabbit)
        })
    # output(results)
    return results

class ThreadedPing(threading.Thread):
    def __init__(self, connection, rabbit):
        threading.Thread.__init__(self)
        self.connection = connection
        self.rabbit = rabbit

    def run(self):
        self.connection.ping_all(self.rabbit)

def threaded_check(connections, rabbit):
    global sig_handler
    # print('Threaded check')
    threads = []
    for connection in connections:
        threads.append(ThreadedPing(connection, rabbit))
        if sig_handler.kill_now:
            break

    for thread in threads:
        thread.start()
        sleep(0.3)

    for thread in threads:
        thread.join()

def monitor(connections, rabbit_config, with_reconnect=False):
    global sig_handler
    rabbit = RabbitConn(rabbit_config)

    while not sig_handler.kill_now:
        # check(connections, rabbit)
        threaded_check(connections, rabbit)
        if with_reconnect:
            rabbit.reconnect_if_needed()

    rabbit.disconnect()


with_reconn = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--with-reconnect',
        action='store_true',
        help=('If set, will attempt to reconnect to rabbit and continue operation if connection is lost.'),
        default=False
    )

    with_reconn = parser.parse_args().with_reconnect


sig_handler = SigHandler(with_reconnect=with_reconn)
connections = []
for connection_config in config['connection_configs']:
    connections.append(Connection(
        connection_config['interface'],
        connection_config['service_name']
    ))

print('{0} Starting monitor on configured interfaces.'.format(datetime.now().isoformat()))
monitor(connections, config['rabbit_config'], with_reconnect=with_reconn)
