FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system networking tools and Python
RUN apt-get update && apt-get install -y \
    nftables \
    iptables \
    iproute2 \
    iputils-ping \
    net-tools \
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
COPY services/firewall-service/firewall_agent.py /opt/viswall/

WORKDIR /opt/viswall

EXPOSE 8081

CMD ["python3", "-u", "firewall_agent.py"]
