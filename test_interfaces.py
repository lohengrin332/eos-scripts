#!/usr/bin/python
from datetime import datetime
from json import load
from os import devnull, path
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
        for ip in config['ips_to_ping']:
            if self.ping(ip):
                success_count += 1
                
        return success_count >= 2
        
    def is_up(self):
        return self.ping_all()
        

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
