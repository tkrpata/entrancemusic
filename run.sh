#!/bin/sh

LOCATION=/home/pi/entrancemusic

cd $LOCATION && python entrance.py &
echo $! > /var/run/entrance.pid
