#!/bin/sh
set -e

# Render nginx configuration with environment variables
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Create certbot webroot directory
mkdir -p /var/www/certbot

# Determine SSL certificate mode
SSL_MODE="${SSL_MODE:-selfsigned}"

if [ "$SSL_MODE" = "letsencrypt" ]; then
    # Production: Use Let's Encrypt
    DOMAIN="${DOMAIN:-localhost}"
    
    if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
        echo "Obtaining Let's Encrypt certificate for $DOMAIN..."
        certbot certonly \
            --standalone \
            --non-interactive \
            --agree-tos \
            --email "${LETSENCRYPT_EMAIL:-admin@$DOMAIN}" \
            -d "$DOMAIN" \
            || {
                echo "Let's Encrypt failed, falling back to self-signed certificate"
                SSL_MODE=selfsigned
            }
    fi
    
    if [ "$SSL_MODE" = "letsencrypt" ]; then
        export SSL_CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
        export SSL_KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    fi
fi

if [ "$SSL_MODE" = "selfsigned" ]; then
    # Development: Use self-signed certificate
    if [ ! -f /etc/nginx/ssl/nginx.crt ]; then
        echo "Generating self-signed SSL certificate..."
        mkdir -p /etc/nginx/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/nginx.key \
            -out /etc/nginx/ssl/nginx.crt \
            -subj "/C=US/ST=State/L=City/O=Viswall/CN=localhost"
    fi
    export SSL_CERT_PATH="/etc/nginx/ssl/nginx.crt"
    export SSL_KEY_PATH="/etc/nginx/ssl/nginx.key"
fi

# Re-render config with SSL paths
envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

echo "Starting nginx with SSL mode: $SSL_MODE"

# Execute the main command
exec "$@"
