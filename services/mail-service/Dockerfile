FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

# Install core packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    # Exim MTA
    exim4-daemon-heavy \
    exim4-config \
    # Courier IMAP/POP3
    courier-base \
    courier-authdaemon \
    courier-authlib \
    courier-authlib-mysql \
    courier-pop \
    courier-imap \
    # Spam/Virus scanning
    spamassassin \
    spamc \
    clamav-daemon \
    clamav-freshclam \
    # Python for agent
    python3.12 \
    python3-pip \
    python3-venv \
    # Mail utilities
    mailutils \
    bsd-mailx \
    # Database
    libdbd-mysql-perl \
    # SSL/TLS
    openssl \
    ca-certificates \
    # System tools
    supervisor \
    cron \
    rsyslog \
    curl \
    netcat-traditional \
    # Build deps
    gcc \
    libffi-dev \
    libssl-dev \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --break-system-packages \
    aiohttp \
    asyncio-mqtt \
    psycopg2-binary \
    sqlalchemy \
    asyncpg \
    pymysql

# Configure SpamAssassin
RUN mkdir -p /var/lib/spamassassin \
    && chmod 755 /var/lib/spamassassin

# Configure ClamAV
RUN mkdir -p /var/run/clamav /var/lib/clamav \
    && chown -R clamav:clamav /var/run/clamav /var/lib/clamav /var/log/clamav

# Setup Exim directories
RUN mkdir -p /var/spool/exim4 /var/log/exim4 /etc/exim4/dkim \
    && chown -R Debian-exim:Debian-exim /var/spool/exim4 /var/log/exim4

# Setup Courier directories
RUN mkdir -p /var/run/courier/authdaemon \
    && chown -R daemon:daemon /var/run/courier

# Create mail storage
RUN mkdir -p /var/mail \
    && chown mail:mail /var/mail

# Copy agent code
COPY services/mail-service/mail_agent.py /opt/viswall/
COPY services/mail-service/entrypoint.sh /opt/viswall/
RUN chmod +x /opt/viswall/entrypoint.sh

# Copy supervisor config
COPY services/mail-service/supervisord.conf /etc/supervisor/conf.d/

# Expose ports
# SMTP
EXPOSE 25 465 587
# POP3/IMAP
EXPOSE 110 995 143 993

# Volume for persistent data
VOLUME ["/var/mail", "/var/log", "/etc/exim4/dkim"]

ENTRYPOINT ["/opt/viswall/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
