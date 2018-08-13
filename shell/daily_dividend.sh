#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py daily_dividend
sleep 1

done
