FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    curl \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    httpx \
    anyio

COPY services/node-agent/viswall_node_agent /opt/viswall/viswall_node_agent

# Runs with NET_ADMIN on the host network namespace; root is required for
# netlink reconfiguration of the host's interfaces and netplan writes.
WORKDIR /opt/viswall

EXPOSE 8085

CMD ["python3", "-m", "uvicorn", "viswall_node_agent.api:app", "--host", "0.0.0.0", "--port", "8085"]
