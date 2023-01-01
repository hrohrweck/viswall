This is an attempt to revive a Linux based security appliance which I developed 15-20 years ago. WIP
First usage will be the mailscanner

Environment variables for startup:
  DB_NAME_SPAMASSASSIN   ... database name for spamassassin db
  DB_NAME_VISWALL        ... database name for viswall db
  DB_NAME_EXIM           ... database name for exim db 
  DB_HOST                ... host name or IP of database host
  DB_USER                ... database username
  DB_PASS                ... corresponding password
  HOSTNAME               ... Hostname associated with instance
  CERT_COUNTRY_CODE      ... country code to use for CA and derived certificates
  CERT_STATE             ... state for CA and derived certificates
  CERT_LOCATION          ... location to use for CA and derived certificates
  CERT_ORGANIZATION      ... organization to use for CA and derived certificates
  CERT_ORGANIZATION_UNIT ... OU to use for CA and derived certificates

In order to access netfilter, "--privileged" is required

Start (example):
  docker run --privileged --restart always --pull always --name exim -d -e HOSTNAE=viswall.local -e CERT_COUNTRY_CODE=AT -e CERT_STATE=UA -e CERT_LOCATION=Steyr -e CERT_ORGANIZATION="visions in mind" -e CERT_ORGANIZATION_UNIT=viswall -e DB_NAME_SPAMASSASSIN=spamassassin -e DB_NAME_VISWALL=viswall -e DB_NAME_EXIM=exim -e DB_HOST=127.0.0.1 -e DB_USER=someuser -e DB_PASS=somepass -v /psmedia/storage/data0/exim4/log:/var/log/exim4 -v /psmedia/storage/data0/exim4/mysql:/var/lib/mysql -v /psmedia/storage/data0/exim4/mail:/var/spool/exim4 -v /psmedia/storage/data0/exim4/mail:/data/mail -p 25:25 -p 465:465 -p 587:587 -p 110:110 -p 143:143 -p 993:993 -p 995:995 exim4:latest

It is possible to provide your own certificate/key by mounting a server.crt and server.key to /viswall/certs, e. g.
  docker run --privileged --restart always --pull always --name exim -d -v /path/to/server.crt:/viswall/certs/server.crt -v /path/to/server.key:/viswall/certs/server.key -e DB_NAME_SPAMASSASSIN=spamassassin -e DB_NAME_VISWALL=viswall -e DB_NAME_EXIM=exim -e DB_HOST=127.0.0.1 -e DB_USER=someuser -e DB_PASS=somepass -v /psmedia/storage/data0/exim4/log:/var/log/exim4 -v /psmedia/storage/data0/exim4/mysql:/var/lib/mysql -v /psmedia/storage/data0/exim4/mail:/var/spool/exim4 -v /psmedia/storage/data0/exim4/mail:/data/mail -p 25:25 -p 465:465 -p 587:587 -p 110:110 -p 143:143 -p 993:993 -p 995:995 exim4:latest

