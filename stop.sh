#!/bin/sh

pid=`cat /var/run/entrance.pid`
kill $pid && rm /var/run/entrance.pid
