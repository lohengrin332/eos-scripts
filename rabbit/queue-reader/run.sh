#!/usr/bin/env bash

/usr/bin/docker run -d --restart unless-stopped --name qreader -d connection-monitor/ssh-qreader:latest

