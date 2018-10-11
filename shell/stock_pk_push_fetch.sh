#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py stock_pk_push
sleep 3

done
