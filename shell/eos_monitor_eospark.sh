#!/bin/sh
while true

do
/data/www/venv/bin/python /data/www/api/manage.py eos_monitor_actions_eospark
sleep 200

done
