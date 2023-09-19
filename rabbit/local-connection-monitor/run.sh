#!/usr/bin/env bash

/usr/bin/docker run -d --restart unless-stopped --name lcm connection-monitor/python-rabbit-local:latest
