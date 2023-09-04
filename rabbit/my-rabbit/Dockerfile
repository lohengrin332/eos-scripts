FROM rabbitmq:3-management-alpine

ENV RABBITMQ_DEFAULT_USER=jlewis
ENV RABBITMQ_DEFAULT_PASS=rabbitmq
ENV RABBITMQ_PID_FILE=/var/lib/rabbitmq/mnesia/rabbitmq
ENV RABBITMQ_SERVICE_USER=eos
ENV RABBITMQ_SERVICE_PASS=eospassword

RUN mkdir -p /rmq

ADD --chmod=755 init.sh /rmq

CMD ["/rmq/init.sh"]
