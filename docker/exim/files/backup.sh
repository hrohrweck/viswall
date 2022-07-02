#!/bin/bash
DBUSER=$1
DBPASSWORD=$2
DATE=$(date +%Y%m%d%H%M%S)
echo "Backing up database"
mysqldump --all-databases -u $DBUSER -p"$DBPASSWORD" >/backups/mysqldump-${DATE}.sql

echo "Backing up spamassassin database"
runuser -u mail -- sa-learn --backup > /backups/spamassassin-bayes-${DATE}.db

echo "Deleting backups older than 14 days"

find /backups/ -ctime 14 -exec rm {} \;
