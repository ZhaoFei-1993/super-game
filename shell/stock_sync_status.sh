#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py stock_synctime
sleep 5

done
