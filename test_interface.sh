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
	/usr/bin/sudo /bin/ping -q -c $COUNT -I $IFACE $TARGET || \
	/bin/ping -q -c $COUNT $TARGET
