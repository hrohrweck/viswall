FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install VPN tools and Python
RUN apt-get update && apt-get install -y \
    wireguard-tools \
    strongswan \
    strongswan-swanctl \
    openvpn \
    xl2tpd \
    ppp \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy agent code
COPY services/vpn-service/vpn_agent.py /opt/viswall/

WORKDIR /opt/viswall

CMD ["python3", "-u", "vpn_agent.py"]
