#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py initial_online_user
sleep 1

done
