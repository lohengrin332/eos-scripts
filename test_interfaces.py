#!/usr/bin/python
from datetime import datetime
from json import load
from os import devnull, path
import signal
from subprocess import call, check_output, Popen, PIPE, STDOUT
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
        self.failure_count = 0

    def get_ip(self):
        if self.ip is None:
            self.ip = check_output(['{sp}/get_ip.sh'.format(sp=script_path), self.interface]).rstrip("\n")
            if self.ip == '':
                self.ip = 'INVALID IFACE'
        return self.ip

    def ping(self, ip, count=3):
        result = call([
            'sudo', 'ping', '-c', str(count), '-I', self.interface, ip,
        ], stdout=DEVNULL, stderr=STDOUT)
        
        return result==0

    def ping_all(self):
        success_count = 0
        self.ping_count += 1
        for ip in config['ips_to_ping']:
            if self.ping(ip):
                success_count += 1
                
        if success_count >= 2:
            return True
        else:
            self.failure_count += 1
            return False

    def get_failure_rate(self):
        return self.failure_count / self.ping_count
        
    def is_up(self):
        return self.ping_all()


class SigHandler:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.kill_now = True
        

connections = []
for connection_config in config['connection_configs']:
    connections.append(Connection(
        connection_config['interface'],
        connection_config['service_name']
    ))

def notify_down(connections):
    command = ['/usr/sbin/ssmtp'] + config['recipients']
    subject = 'Internet connection is unstable'
    connection_format = '{name} is down!'
    body = []
    for connection in connections:
        body.append(connection_format.format(name=connection.service_name))

    message = b'From: {sender}\nTo: {recipients}\nSubject: {subject}\n{body}\n'.format(
        sender=config['sender'],
        recipients=', '.join(config['recipients']),
        subject=subject,
        body='\n'.join(body + ['Timestamp - {}'.format(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))]),
    )

    if config['debug']:
        print message

    send_process = Popen(
        command,
        stdout=DEVNULL,
        stderr=STDOUT,
        stdin=PIPE,
    )
    send_process.communicate(input=message)

def check_connections(connections):
    failed_connections = []
    for connection in connections:
        if config['debug']:
            print 'Checking %s %15s %s' % (
                connection.interface,
                connection.get_ip(),
                connection.service_name,
            )

        if not connection.is_up():
            failed_connections.append(connection)

    return failed_connections

def monitor(connections):
    sig_handler = SigHandler()
    while not sig_handler.kill_now:
        # if config['debug']:
        #     sig_handler.exit_gracefully()
        failed_connections = check_connections(connections)
        for connection in failed_connections:
            print b'\n{service_name} failed'.format(connection.service_name)
        else:
            print 'Stable'

    print ''
    for connection in connections:
        print b'{service_name:<10} had a {failure_rate:6.2f}% failure rate.'.format(
            service_name=connection.service_name,
            failure_rate=connection.get_failure_rate()
        )

def check(connections):
    connections_to_retry = check_connections(connections)

    cnt_need_retry = len(connections_to_retry)
    if cnt_need_retry > 0:
        if config['debug']:
            print b'\n{cnt} connections failed first attempt\n'.format(cnt=cnt_need_retry)

        sleep(5)

        connections_to_notify = check_connections(connections_to_retry)

        if config['debug']:
            print '\n{cnt} connections failed second attempt\n'.format(cnt=len(connections_to_notify))

        notify_down(connections_to_notify)


monitor(connections)
