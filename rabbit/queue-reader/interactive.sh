#!/usr/bin/env bash

/usr/bin/docker run -it --restart unless-stopped --name qreader -d connection-monitor/ssh-qreader:latest
