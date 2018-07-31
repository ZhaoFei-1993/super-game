#!/bin/sh
while true

do
/data/www/gsg/venv/bin/python /data/www/gsg/api/manage.py eth_monitor
sleep 5

done