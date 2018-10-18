#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py stock_recording
sleep 120

done
