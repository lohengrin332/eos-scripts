#!/bin/bash

IFACE=$1
shift
COUNT=$1
shift
TARGET=$1
shift

if [ -z "$IFACE" ] || [ -z "$COUNT" ] || [ -z "$TARGET" ]; then
	echo "USAGE: $0 <IFACE> <COUNT> <TARGET_IP>"
	exit 1
fi

/bin/uname -a | /bin/grep UBNT &>/dev/null && \
	PING_COMMAND=/usr/bin/sudo /bin/ping -q -c $COUNT -I $IFACE $TARGET || \
	PING_COMMAND=/bin/ping -q -c $COUNT $TARGET

if [ "$1" == "--loop" ]; then
	while true; do
		`${PING_COMMAND}`
	done
else
	`${PING_COMMAND}`
fi
