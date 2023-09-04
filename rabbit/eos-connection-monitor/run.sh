#!/usr/bin/env bash

/usr/bin/docker run -d --restart unless-stopped --name ecm -d connection-monitor/ssh-eos:latest
