FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bind9 \
    bind9-utils \
    dnsutils \
    python3 \
    python3-pip \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    anyio

COPY services/dns-service/viswall_dns_agent /opt/viswall/viswall_dns_agent
COPY services/dns-service/entrypoint.sh /opt/viswall/entrypoint.sh
COPY services/dns-service/supervisord.conf /etc/supervisor/conf.d/viswall.conf

RUN chmod +x /opt/viswall/entrypoint.sh \
    && mkdir -p /var/lib/bind/viswall-zones /var/lib/bind/keys /var/cache/bind \
    && chown -R bind:bind /var/lib/bind /var/cache/bind /etc/bind

EXPOSE 53/udp 53/tcp 8082

ENTRYPOINT ["/opt/viswall/entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
