#!/bin/sh

( \
	rabbitmqctl wait --timeout 60 $RABBITMQ_PID_FILE ; \
	rabbitmqctl add_user $RABBITMQ_SERVICE_USER $RABBITMQ_SERVICE_PASS ; \
	rabbitmqctl set_permissions -p / $RABBITMQ_SERVICE_USER ".*" ".*" ".*" ; \
	echo "*** User $RABBITMQ_SERVICE_USER created. ***"
) &

rabbitmq-server $@
