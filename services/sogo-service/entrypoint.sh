#!/bin/bash
set -e

# Render configuration template with environment variables
envsubst < /etc/sogo/sogo.conf.template > /etc/sogo/sogo.conf

# Create required directories
mkdir -p /var/run/sogo
mkdir -p /var/log/sogo
mkdir -p /var/spool/sogo

# Set permissions
chown -R sogo:sogo /var/run/sogo
chown -R sogo:sogo /var/log/sogo
chown -R sogo:sogo /var/spool/sogo
chown sogo:sogo /etc/sogo/sogo.conf

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL at ${SOGO_DB_HOST}:5432..."
while ! nc -z "${SOGO_DB_HOST}" 5432; do
  sleep 1
done
echo "PostgreSQL is ready"

# Create SOGo database tables if they don't exist
# SOGo will auto-create tables on first access, but we can pre-warm them
echo "SOGo configuration complete. Starting SOGo..."

# Execute the main command
exec "$@"
