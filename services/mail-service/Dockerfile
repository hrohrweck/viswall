FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

# Exim MTA + Dovecot IMAP/POP3/LMTP (Postgres auth) + spam/virus (D2: single Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    exim4-daemon-heavy \
    exim4-config \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    dovecot-pgsql \
    spamassassin \
    spamc \
    spamd \
    clamav-daemon \
    clamav-freshclam \
    python3 \
    python3-pip \
    postgresql-client \
    openssl \
    ca-certificates \
    supervisor \
    rsyslog \
    cron \
    curl \
    netcat-traditional \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    aiohttp \
    psycopg2-binary \
    sqlalchemy \
    asyncpg

# Virtual mail user for maildir storage
RUN groupadd -g 5000 vmail && \
    useradd -g 5000 -u 5000 -d /var/mail/vhosts -m -s /usr/sbin/nologin vmail
RUN usermod -aG Debian-exim clamav

RUN mkdir -p /var/lib/spamassassin && chmod 755 /var/lib/spamassassin && \
    mkdir -p /var/run/clamav /var/lib/clamav && \
    (chown -R clamav:clamav /var/run/clamav /var/lib/clamav /var/log/clamav || true) && \
    mkdir -p /var/spool/exim4 /var/log/exim4 && \
    chown -R Debian-exim:Debian-exim /var/spool/exim4 /var/log/exim4 && \
    mkdir -p /var/mail/vhosts && chown vmail:vmail /var/mail/vhosts && \
    mkdir -p /etc/dovecot/ssl /var/run/dovecot

COPY services/mail-service/mail_agent.py /opt/viswall/
COPY services/mail-service/config/ /opt/viswall/config/
COPY services/mail-service/entrypoint.sh /opt/viswall/
RUN chmod +x /opt/viswall/entrypoint.sh
COPY services/mail-service/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# SMTP + IMAP/POP3 (POP3 kept per D4)
EXPOSE 25 465 587 110 995 143 993

VOLUME ["/var/mail", "/var/log/exim4"]

ENTRYPOINT ["/opt/viswall/entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
