#!/bin/bash

IFACE=$1
shift
COUNT=$1
shift
TARGET=$1
shift

if [ -z "$IFACE" ] || [ -z "$COUNT" ] || [ -z "$TARGET" ]; then
	echo "USAGE: $0 <IFACE> <COUNT> <TARGET_IP> [--loop]"
	exit 1
fi

/bin/uname -a | /bin/grep UBNT &>/dev/null && \
	SYSTEM='eos' || \
	SYSTEM='linux'

ping_func() {
	if [ $SYSTEM == 'eos' ]; then
		/usr/bin/sudo /bin/ping -q -c $COUNT -I $IFACE $TARGET
	else
		/usr/bin/ping -q -c $COUNT $TARGET
	fi
}

if [ "$1" == "--loop" ]; then
	while true; do
		ping_func | grep -e 'packets transmitted\|rtt min'
		echo
		sleep 0.25
	done
else
	ping_func
fi
