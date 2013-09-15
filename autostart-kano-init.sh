#!/bin/sh

ENABLED=0
if [ `id -u` -eq 0 -a $ENABLED -eq 1 ]; then
    kano-init
    kill -HUP $PPID
fi
