#!/usr/bin/env bash

/usr/bin/docker run -d --restart unless-stopped --name lcm -d connection-monitor/python-rabbit-local
