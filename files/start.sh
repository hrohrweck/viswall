#!/bin/bash
cat /etc/courier/templates/authmysqlrc.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /etc/courier/authmysqlrc

cat /etc/exim4/exim4.conf.template.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /etc/exim4/exim4.conf.template
update-exim4.conf

cat /viswall/scripts/exim/cleanup.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/scripts/exim/cleanup
chmod +x /viswall/scripts/exim/cleanup

cat /viswall/scripts/exim/malwarereport/templates/config.php.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/scripts/exim/malwarereport/config.php

cat /viswall/config.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/config

cat /viswall/viswall-web/config.php.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/viswall-web/config.php

/usr/bin/supervisord

