#!/usr/bin/env bash

/usr/bin/ssh -i ./.ssh/eos_rsa qreader@rpi.lan /home/qreader/bin/queue_reader.py
