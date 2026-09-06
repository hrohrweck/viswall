#!/bin/bash
set -euo pipefail

# --- rndc control key: deterministic single source -----------------------
# named loads /etc/bind/rndc.key via the include rendered in
# named.conf.options; rndc reads /etc/bind/rndc.conf which includes the same
# key file. Generate once, keep across restarts via the /etc/bind volume.
if [ ! -f /etc/bind/rndc.key ]; then
  echo "[entrypoint] generating rndc key"
  SECRET=$(rndc-confgen -k rndc-key 2>/dev/null | awk '/secret/ {gsub(/"/, "", $3); print $3}')
  cat > /etc/bind/rndc.key <<EOF
key "rndc-key" {
    algorithm hmac-sha256;
    secret "${SECRET}";
};
EOF
  chmod 640 /etc/bind/rndc.key
  chown root:bind /etc/bind/rndc.key || true
fi

# rndc.conf has no include support (unlike named.conf), so the key block is
# duplicated verbatim from rndc.key; named loads the key via include in
# named.conf.options and this file drives the rndc CLI side.
{
  cat /etc/bind/rndc.key
  printf '\noptions {\n    default-key "rndc-key";\n    default-server 127.0.0.1;\n    default-port 953;\n};\n'
} > /etc/bind/rndc.conf
chmod 644 /etc/bind/rndc.conf

# --- writable dirs for named (runs as user "bind") ------------------------
mkdir -p /run/named "${ZONES_DIR:-/var/lib/bind/viswall-zones}" "${DNS_KEYS_DIR:-/var/lib/bind/keys}" /var/cache/bind
chown bind:bind /run/named "${ZONES_DIR:-/var/lib/bind/viswall-zones}" "${DNS_KEYS_DIR:-/var/lib/bind/keys}" /var/cache/bind /etc/bind

# --- validate stock config before supervisord takes over ------------------
if command -v named-checkconf >/dev/null 2>&1; then
  if named-checkconf /etc/bind/named.conf; then
    echo "[entrypoint] named config OK"
  else
    echo "[entrypoint] WARNING: named-checkconf failed — named may fail to start"
  fi
fi

exec "$@"
