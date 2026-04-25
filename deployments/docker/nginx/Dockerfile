FROM nginx:alpine

# Install certbot for Let's Encrypt and envsubst
RUN apk add --no-cache certbot certbot-nginx gettext openssl

# Copy nginx configuration template
COPY deployments/docker/nginx/nginx.conf.template /etc/nginx/nginx.conf.template

# Copy entrypoint script
COPY deployments/docker/nginx/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose HTTP and HTTPS ports
EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
