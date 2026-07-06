#!/bin/bash
set -euo pipefail

: "${SOGO_DB_HOST:=postgres}"
: "${SOGO_DB_NAME:=viswall}"
: "${SOGO_DB_USER:=viswall}"
: "${SOGO_DB_PASS:?SOGO_DB_PASS is required}"
: "${SOGO_TIMEZONE:=UTC}"

sed -e "s|\${SOGO_DB_HOST}|${SOGO_DB_HOST}|g" \
    -e "s|\${SOGO_DB_NAME}|${SOGO_DB_NAME}|g" \
    -e "s|\${SOGO_DB_USER}|${SOGO_DB_USER}|g" \
    -e "s|\${SOGO_DB_PASS}|${SOGO_DB_PASS}|g" \
    -e "s|\${SOGO_TIMEZONE}|${SOGO_TIMEZONE}|g" \
    /etc/sogo/sogo.conf.template > /etc/sogo/sogo.conf

mkdir -p /var/run/sogo /var/log/sogo /var/spool/sogo
chown -R sogo:sogo /var/run/sogo /var/log/sogo /var/spool/sogo /etc/sogo/sogo.conf || true

# SOGo uses memcached for session storage
memcached -d -u nobody -m 64 -l 127.0.0.1 -p 11211 >/dev/null 2>&1 || memcached -d -m 64 -l 127.0.0.1 -p 11211 >/dev/null 2>&1 || true

echo "Waiting for PostgreSQL at ${SOGO_DB_HOST}:5432..."
for _ in $(seq 1 60); do
  if (exec 3<>/dev/tcp/${SOGO_DB_HOST}/5432) 2>/dev/null; then exec 3>&-; echo "PostgreSQL is ready"; break; fi
  sleep 2
done

set +u
. /usr/share/GNUstep/Makefiles/GNUstep.sh
set -u

export LD_PRELOAD=/usr/lib/bindfix.so

echo "SOGo configuration complete. Starting SOGo..."
exec gosu sogo "$@"
