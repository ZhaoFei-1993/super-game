#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py online_number_fluctuations
sleep 300

done

