FROM alpine

VOLUME /qreader
RUN apk add --update --no-cache openssh

RUN /bin/mkdir /root/.ssh
ADD known_hosts /root/.ssh/
ADD eos_rsa /root/.ssh/

WORKDIR /root

CMD /usr/bin/ssh -i /root/.ssh/eos_rsa qreader@rpi.lan /home/qreader/bin/queue_reader.py
# CMD /bin/sh
