#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py bch_monitor
sleep 5

done