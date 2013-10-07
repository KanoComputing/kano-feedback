#!/bin/sh

# 0: Disabled
# 1: Name
# 2: Rabbit
# 3: Bomb
STAGE=0

if [ `id -u` -eq 0 -a "$STAGE" -gt 0 ]; then
    kano-init "$STAGE"
    kill -HUP $PPID
fi
