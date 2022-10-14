#!/usr/bin/env python

from json import load, dumps
from os import devnull, path
import pika
import signal
from subprocess import call, check_output, STDOUT

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

    def ping_all(self):
        self.ping_count += 1
        results = []
        for ip in config['ips_to_ping']:
            results.append({
                'interface': self.get_interface(),
                'service_name': self.get_service_name(),
                'target': ip,
                'result': self.ping(ip)
            })
        return results


class SigHandler:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True


class RabbitConn:
    consumer_tag = None

    def __init__(self, rabbit_config):
        credentials = pika.PlainCredentials(rabbit_config['user'], rabbit_config['password'])
        parameters = pika.ConnectionParameters(host=rabbit_config['host'], credentials=credentials)
        self.queue = 'test_q' # rabbit_config['queue']
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


def output(results):
    print dumps(results)

def check(connections):
    results = []
    for connection in connections:
        results.append({
            'service_name': connection.get_service_name(),
            'interface': connection.get_interface(),
            'results': connection.ping_all()
        })
    # output(results)
    return results

def monitor(connections, rabbit_config):
    sig_handler = SigHandler()
    rabbit = RabbitConn(rabbit_config)

    while not sig_handler.kill_now:
        for result in (check(connections)):
            rabbit.send(result)

    rabbit.disconnect()


connections = []
for connection_config in config['connection_configs']:
    connections.append(Connection(
        connection_config['interface'],
        connection_config['service_name']
    ))

monitor(connections, config['rabbit_config'])
check(connections)
