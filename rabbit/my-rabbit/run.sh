#!/usr/bin/env bash

/usr/bin/docker run -d --restart unless-stopped --hostname hydra-rabbit --name hydra-rabbit -p 5672:5672 -p 15672:15672 connection-monitor/my-rabbit
