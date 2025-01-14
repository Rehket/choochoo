#!/bin/bash

# this is so matplotlib can write it's config (we're running as non-root)
export MPLCONFIGDIR=/data/.config

CH2="ch2 --base /data --db-bind postgresql"

echo "waiting for database"
sleep 5

echo "forcing database (will give errors if already exists)"
$CH2 -v0 db add user
$CH2 -v0 db add database

CMD="$CH2 --dev web service --web-bind 0.0.0.0 --warn-data --warn-secure"
echo -e "\nrunning $CMD\n"

eval $CMD
