#!/bin/bash
cat /etc/courier/templates/authmysqlrc.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /etc/courier/authmysqlrc

cat /etc/exim4/exim4.conf.template.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /etc/exim4/exim4.conf.template
update-exim4.conf

cat /viswall/scripts/exim/cleanup.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/scripts/exim/cleanup
chmod +x /viswall/scripts/exim/cleanup

cat /viswall/scripts/exim/malwarereport/templates/config.php.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/scripts/exim/malwarereport/config.php

cat /viswall/config.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/config

cat /viswall/viswall-web/config.php.template |sed "s/##DB_NAME_SPAMASSASSIN##/${DB_NAME_SPAMASSASSIN}/g" |sed "s/##DB_NAME_VISWALL##/${DB_NAME_VISWALL}/g" |sed "s/##DB_NAME_EXIM##/${DB_NAME_EXIM}/g" |sed "s/##DB_HOST##/${DB_HOST}/g" |sed "s/##DB_USER##/${DB_USER}/g" |sed "s/##DB_PASS##/${DB_PASS}/g" > /viswall/viswall-web/config.php

if [ -e $CERT_COUNTRY_CODE ]
then
    CERT_COUNTRY_CODE="AT"
fi

if [ -e $CERT_STATE ]
then
    CERT_STATE="upper austria"
fi

if [ -e $CERT_LOCATION ]
then
    CERT_LOCATION="Steyr"
fi

if [ -e $CERT_ORGANIZATION ]
then
    CERT_ORGANIZATION="visions in mind"
fi

if [ -e $CERT_ORGANIZATION_UNIT ]
then
    CERT_ORGANIZATION_UNIT="viswall"
fi

if [ -e $HOSTNAME ]
then
    HOSTNAME="viswall.local"
fi

# create CA
mkdir -p /viswall/certs/ca
cd /viswall/certs
openssl req -x509 \
            -sha256 -days 3650 \
            -nodes \
            -newkey rsa:2048 \
            -subj "/CN=${HOSTNAME}/C=${CERT_COUNTRY_CODE}/L=${CERT_LOCATION}" \
            -keyout ca/viswallRootCA.key -out ca/viswallRootCA.crt 

if [ ! -e server.crt ]
then
    # create self signed certs
    openssl genrsa -out server.key 2048

    cat > csr.conf <<EOF
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = ${CERT_COUNTRY_CODE}
ST = ${CERT_STATE}
L = ${CERT_LOCATION}
O = ${CERT_ORGANIZATION}
OU = ${CERT_ORGANIZATION_UNIT}
CN = ${HOSTNAME}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
IP.1 = $(hostname -I)

EOF

    openssl req -new -key server.key -out server.csr -config csr.conf

    cat > cert.conf <<EOF

authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${HOSTNAME}

EOF

    openssl x509 -req \
        -in server.csr \
        -CA ca/viswallRootCA.crt -CAkey ca/viswallRootCA.key \
        -CAcreateserial -out server.crt \
        -days 3650 \
        -sha256 -extfile cert.conf
fi

cp server.crt /etc/exim4/exim.crt
cp server.key /etc/exim4/exim.key
cat /etc/exim4/exim.key >/etc/courier/imapd.pem
cat /etc/exim4/exim.crt >>/etc/courier/imapd.pem
cp /etc/courier/imapd.pem /etc/courier/pop3d.pem
chmod +r /etc/exim4/exim.crt && chmod +r /etc/exim4/exim.key
chgrp courier /etc/courier/imapd.pem
chmod g+r /etc/courier/imapd.pem && \
chgrp courier /etc/courier/pop3d.pem
chmod g+r /etc/courier/pop3d.pem && \

cd /viswall
/usr/bin/supervisord

