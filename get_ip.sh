#!/bin/vbash

IFACE=$1
shift

/opt/vyatta/bin/vyatta-op-cmd-wrapper show interfaces ethernet $IFACE \
	| grep -e 'inet\b' \
	| awk '{ print $2 }' \
	| sed 's#/[0-9]\+$##'
