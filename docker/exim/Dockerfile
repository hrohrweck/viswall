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
COPY files/viswall.tar.bz2 /tmp/setup/
COPY files/fetchmail/fetchmail.conf /etc/
RUN chown -R Debian-exim.Debian-exim /etc/fetchmail.conf && chmod 700 /etc/fetchmail.conf
COPY files/clamav/clamd.conf /etc/clamav/
COPY files/clamav/freshclam.conf /etc/clamav/
COPY files/exim/exim4.conf.template /etc/exim4/
COPY files/exim/exim.filter /etc/exim4/
COPY files/certs/exim.crt /etc/exim4/
COPY files/certs/exim.key /etc/exim4/
RUN cd / && tar xvfj /tmp/setup/viswall.tar.bz2
RUN update-exim4.conf
COPY files/start.sh /usr/bin/
RUN chmod +x /usr/bin/start.sh && \
    mkdir -p /var/run/clamav && chown Debian-exim /var/log/exim4 && \
    mkdir -p /var/run/mysqld && chown mysql.mysql /var/run/mysqld && \
    mkdir -p /var/log/clamav && chown -R clamav /var/log/clamav && mkdir -p /var/run/clamav && \
    chown -R clamav /var/run/clamav && /usr/bin/freshclam && chown -R clamav /var/run/clamav && \
    mkdir -p /var/run/courier && chown -R daemon.daemon /var/run/courier
RUN cpan App::cpanminus && cpanm install --notest Mail::SPF && cpanm install --notest Mail::SPF::Query
COPY files/courier/* /etc/courier/
COPY files/cron/* /etc/cron.d
RUN chmod 644 /etc/cron.d/*
RUN ln -s /viswall/scripts/exim/learn-ham /etc/cron.hourly/ && \
    ln -s /viswall/scripts/exim/learn-spam /etc/cron.hourly/
RUN cat /etc/exim4/exim.key >/etc/courier/pop3d.pem && \
    cat /etc/exim4/exim.crt >>/etc/courier/pop3d.pem && \
    chgrp courier /etc/courier/pop3d.pem && \
    chmod g+r /etc/courier/pop3d.pem && \
    cat /etc/exim4/exim.key >/etc/courier/imapd.pem && \
    cat /etc/exim4/exim.crt >>/etc/courier/imapd.pem && \
    chgrp courier /etc/courier/imapd.pem && \
    chmod g+r /etc/courier/imapd.pem   
COPY files/malwarereport/* /viswall/scripts/exim/malwarereport/
RUN cd /viswall/scripts/exim/malwarereport && /usr/bin/composer require phpmailer/phpmailer
COPY files/exim/cleanup /viswall/scripts/exim/
RUN chmod +x /viswall/scripts/exim/cleanup

COPY files/supervisord/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord"]
#ENTRYPOINT ["/usr/bin/start.sh"]
