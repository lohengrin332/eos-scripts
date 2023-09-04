FROM python:3.9.13-alpine
VOLUME /lcm
RUN /usr/local/bin/pip install pika
ADD local_connection_monitor.py test_interfaces.config.json /lcm/
WORKDIR /lcm
CMD ./local_connection_monitor.py
# CMD /bin/sh
