FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true
ENV PERL_MM_USE_DEFAULT=1
ENV PERL_CPANM_OPT=--notest

RUN echo "tzdata tzdata/Areas select Europe" >/tmp/preseed.txt && \
    echo "tzdata tzdata/Zones/Europe select Vienna" >>/tmp/preseed.txt
RUN debconf-set-selections /tmp/preseed.txt && \
    apt update -y && \
    apt upgrade -y && \
    apt install -y \
               mariadb-client mariadb-common mariadb-server \
               clamav clamav-daemon clamav-freshclam \
               exim4 exim4-base exim4-config exim4-daemon-heavy \
               spamassassin \
               php php-cli php-common php-mysql libphp-phpmailer composer \
               cron \
               rsyslog \
               nano \
               fetchmail \
               spfquery opendmarc \
               fail2ban iptables \
               supervisor
RUN touch /usr/share/man/man5/maildir.courier.5.gz && \
    touch /usr/share/man/man8/deliverquota.courier.8.gz && \
    touch /usr/share/man/man1/maildirmake.courier.1.gz && \
    touch /usr/share/man/man7/maildirquota.courier.7.gz && \
    touch /usr/share/man/man1/makedat.courier.1.gz && \
    apt install -y courier-base courier-authdaemon courier-authlib courier-authlib-mysql courier-authlib-userdb courier-pop courier-imap
RUN mkdir -p /var/run/courier/authdaemon && mkdir -p /var/log/supervisor \
    mkdir -p /tmp/setup && mkdir -p /var/log/console
COPY files/backup.sh /etc/cron.daily/
RUN chmod +x /etc/cron.daily/backup.sh
ADD source /tmp/setup
COPY files/clamav/clamd.conf /etc/clamav/
COPY files/clamav/freshclam.conf /etc/clamav/
COPY files/exim/templates/exim4.conf.template /etc/exim4/exim4.conf.template.template
COPY files/exim/exim.filter /etc/exim4/
RUN mkdir -p /viswall && mv /tmp/setup/* /viswall/
COPY files/config.php.template /viswall/viswall-web/
COPY files/config.template /viswall/
RUN mkdir -p /var/run/clamav && chown Debian-exim /var/log/exim4 && \
    mkdir -p /var/run/mysqld && chown mysql.mysql /var/run/mysqld && \
    mkdir -p /var/log/clamav && chown -R clamav /var/log/clamav && mkdir -p /var/run/clamav && \
    chown -R clamav /var/run/clamav && /usr/bin/freshclam && chown -R clamav /var/run/clamav && \
    mkdir -p /var/run/courier && chown -R daemon.daemon /var/run/courier
RUN cpan App::cpanminus && cpanm install --notest Mail::SPF && cpanm install --notest Mail::SPF::Query && cpan install Config::File
COPY files/courier/* /etc/courier/
RUN chmod +x /etc/courier/imap-supervisord && chmod +x /etc/courier/imap-ssl-supervisord && chmod +x /etc/courier/pop3-supervisord && chmod +x /etc/courier/pop3-ssl-supervisord
RUN mkdir -p /etc/courier/templates
COPY files/courier/templates/* /etc/courier/templates/
COPY files/cron/* /etc/cron.d
RUN chmod 644 /etc/cron.d/*
RUN ln -s /viswall/scripts/exim/learn-ham /etc/cron.hourly/ && \
    ln -s /viswall/scripts/exim/learn-spam /etc/cron.hourly/
COPY files/malwarereport/* /viswall/scripts/exim/malwarereport/
RUN mkdir -p /viswall/scripts/exim/malwarereport/templates
COPY files/malwarereport/templates/* /viswall/scripts/exim/malwarereport/templates/
RUN cd /viswall/scripts/exim/malwarereport && /usr/bin/composer require phpmailer/phpmailer
RUN mkdir -p /viswall/scripts/exim
COPY files/exim/templates/cleanup.template /viswall/scripts/exim/

RUN mkdir -p /var/run/fail2ban && rm -f /etc/fail2ban/jail.d/defaults-debian.conf
COPY files/fail2ban/filter.d/exim.conf /etc/fail2ban/filter.d/
COPY files/fail2ban/jail.local /etc/fail2ban/jail.d/exim.conf

COPY files/supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY files/start.sh /opt/    
RUN chmod +x /opt/start.sh

CMD ["/opt/start.sh"]
