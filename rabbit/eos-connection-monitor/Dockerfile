FROM alpine

VOLUME /ecm
RUN apk add --update --no-cache openssh

ADD eos_rsa /ecm

RUN /bin/mkdir /root/.ssh
ADD known_hosts /root/.ssh/

WORKDIR /ecm

CMD /usr/bin/ssh -i ./eos_rsa ecm@eos.lan /config/scripts/custom/monitor_interfaces.py
# CMD /bin/sh
