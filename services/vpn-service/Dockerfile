FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install WireGuard tooling and Python. The agent manages ONLY the
# WireGuard site-to-site client (wg show/genkey + wg-quick@client via
# nsenter) and reads interface state via `ip -j` (iproute2); the legacy
# strongswan/openvpn/xl2tpd/ppp stack was dropped with the old vpn_agent.py.
RUN apt-get update && apt-get install -y \
    wireguard-tools \
    iproute2 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --break-system-packages \
    fastapi \
    uvicorn \
    pydantic

# Copy agent code
COPY services/vpn-service/viswall_vpn_agent /opt/viswall/viswall_vpn_agent

WORKDIR /opt/viswall

EXPOSE 8083

CMD ["python3", "-u", "-m", "viswall_vpn_agent"]
