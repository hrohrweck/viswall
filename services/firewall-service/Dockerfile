FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system networking tools and Python.
# curl: gateway-health probes on the host network; dbus + libdbus-1-3:
# host D-Bus access from the host-net container.
RUN apt-get update && apt-get install -y \
    nftables \
    iptables \
    iproute2 \
    iputils-ping \
    net-tools \
    curl \
    dbus \
    libdbus-1-3 \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --break-system-packages \
    fastapi \
    uvicorn \
    pydantic

# Copy agent code
COPY services/firewall-service/viswall_firewall_agent /opt/viswall/viswall_firewall_agent

WORKDIR /opt/viswall

EXPOSE 8081

CMD ["python3", "-u", "-m", "viswall_firewall_agent"]
