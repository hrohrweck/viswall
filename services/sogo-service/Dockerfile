FROM mailcow/sogo:latest

# Install envsubst for template rendering
RUN apt-get update && apt-get install -y gettext-base && rm -rf /var/lib/apt/lists/*

# Copy configuration template and entrypoint
COPY services/sogo-service/sogo.conf.template /etc/sogo/sogo.conf.template
COPY services/sogo-service/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# SOGo runs on port 20000 internally
EXPOSE 20000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sogod", "-WONoDetach", "YES", "-WOPidFile", "/var/run/sogo/sogo.pid", "-WOLogFile", "/var/log/sogo/sogo.log"]
