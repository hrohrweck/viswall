#!/bin/bash
set -euo pipefail

: "${DB_HOST:=postgres}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=viswall}"
: "${DB_USER:=viswall}"
: "${DB_PASS:=}"
: "${EXIM_HOSTNAME:=mail.example.com}"
: "${MAIL_STORAGE:=/var/mail/vhosts}"
: "${DKIM_DOMAIN:=}"

echo "[entrypoint] host=${EXIM_HOSTNAME} db=${DB_HOST}:${DB_PORT}/${DB_NAME} user=${DB_USER}"

mkdir -p /etc/exim4 /etc/dovecot/ssl /var/run/dovecot "${MAIL_STORAGE}"

# --- TLS: mounted certs preferred, else self-signed so the stack always starts ---
if [ -f /viswall/certs/server.crt ] && [ -f /viswall/certs/server.key ]; then
  cp /viswall/certs/server.crt /etc/dovecot/ssl/server.crt
  cp /viswall/certs/server.key /etc/dovecot/ssl/server.key
else
  echo "[entrypoint] no mounted certs -> generating self-signed"
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
    -subj "/CN=${EXIM_HOSTNAME}" \
    -keyout /etc/dovecot/ssl/server.key -out /etc/dovecot/ssl/server.crt >/dev/null 2>&1
fi
cp /etc/dovecot/ssl/server.crt /etc/exim4/tls.crt
cp /etc/dovecot/ssl/server.key /etc/exim4/tls.key
chown Debian-exim:Debian-exim /etc/exim4/tls.crt /etc/exim4/tls.key || true
chmod 600 /etc/exim4/tls.key /etc/dovecot/ssl/server.key

# DKIM key staging: mount is RO/root-owned; Exim runs as Debian-exim and must read it.
if [ -f /opt/viswall/dkim-staging/viswall.private ]; then
  mkdir -p /etc/exim4/dkim
  cp /opt/viswall/dkim-staging/viswall.private /etc/exim4/dkim/viswall.private
  chown Debian-exim:Debian-exim /etc/exim4/dkim/viswall.private
  chmod 0400 /etc/exim4/dkim/viswall.private
else
  echo "[entrypoint] WARNING: no DKIM staging key — outbound mail will be unsigned"
fi

# --- render templated configs (token subst; avoids clobbering exim ${...}) ---
PG_SERVERS="${DB_HOST}::${DB_PORT}/${DB_NAME}/${DB_USER}/${DB_PASS}"
# Write passfile for Dovecot's libpq connection (avoids inline password in config)
echo "${DB_HOST}:${DB_PORT}:${DB_NAME}:${DB_USER}:${DB_PASS}" > /tmp/dovecot.pgpass
chmod 600 /tmp/dovecot.pgpass
render() {
  sed -e "s|@@PG_SERVERS@@|${PG_SERVERS}|g" \
      -e "s|@@PRIMARY_HOSTNAME@@|${EXIM_HOSTNAME}|g" \
      -e "s|@@DB_HOST@@|${DB_HOST}|g" \
      -e "s|@@DB_PORT@@|${DB_PORT}|g" \
      -e "s|@@DB_NAME@@|${DB_NAME}|g" \
      -e "s|@@DB_USER@@|${DB_USER}|g" \
      -e "s|@@DB_PASS@@|${DB_PASS}|g" \
      -e "s|@@MAIL_STORAGE@@|${MAIL_STORAGE}|g" \
      -e "s|@@DKIM_DOMAIN@@|${DKIM_DOMAIN}|g" \
      "$1"
}
render /opt/viswall/config/exim4.conf.tmpl            > /etc/exim4/exim4.conf
echo "/etc/exim4/exim4.conf" > /etc/exim4/trusted_configs; chown root:root /etc/exim4/exim4.conf /etc/exim4/trusted_configs; chmod 644 /etc/exim4/trusted_configs
cp     /opt/viswall/config/dovecot.conf               /etc/dovecot/dovecot.conf
render /opt/viswall/config/dovecot-sql.conf.ext.tmpl  > /etc/dovecot/dovecot-sql.conf.ext
chmod 600 /etc/dovecot/dovecot-sql.conf.ext

chown -R vmail:vmail "${MAIL_STORAGE}"

# --- wait for Postgres so auth/lookups work at start ---
echo "[entrypoint] waiting for postgres ${DB_HOST}:${DB_PORT} ..."
for _ in $(seq 1 60); do
  if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; then
    echo "[entrypoint] postgres is ready"; break
  fi
  sleep 2
done

# --- validate configs (non-fatal) ---
exim4 -C /etc/exim4/exim4.conf -bV >/dev/null 2>&1 && echo "[entrypoint] exim config OK" || echo "[entrypoint] WARNING: exim config check failed"
doveconf -n >/dev/null 2>&1 && echo "[entrypoint] dovecot config OK" || echo "[entrypoint] WARNING: dovecot config check failed"

exec "$@"
