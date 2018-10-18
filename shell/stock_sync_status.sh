#!/bin/sh
while true

do
/data/www/gsg/venv/bin/python /data/www/gsg/api/manage.py stock_synctime
sleep 5

done
