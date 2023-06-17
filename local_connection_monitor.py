#!/usr/bin/env python

from json import dumps, load
from os import devnull, path
import pika
import signal
from subprocess import run, DEVNULL, STDOUT
from time import sleep


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


def ping_all(ips_to_ping, rabbit):
    global sig_handler
    for ip in (ips_to_ping):
        result = {
            'interface': 'local',
            'service_name': 'local',
            'target': ip,
            'result': run(['ping', '-q', '-c', '1', ip], stdout=DEVNULL, stderr=STDOUT).returncode == 0
        }

        rabbit.send(result)

        sleep(2)
        if sig_handler.kill_now:
            break


def monitor(config):
    global sig_handler
    sig_handler = SigHandler()
    rabbit = RabbitConn(config['rabbit_config'])

    while not sig_handler.kill_now:
        ping_all(config['ips_to_ping'], rabbit)

    rabbit.disconnect()


script_path = path.dirname(path.abspath(__file__))

with open('{sp}/test_interfaces.config.json'.format(sp=script_path), 'r') as f:
    config = load(f)

DEVNULL = open(devnull, 'w')

monitor(config)
