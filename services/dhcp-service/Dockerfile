FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    kea-dhcp4-server \
    kea-dhcp6-server \
    kea-ctrl-agent \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    fastapi \
    uvicorn \
    pydantic

COPY services/dhcp-service/dhcp_agent.py /opt/viswall/

WORKDIR /opt/viswall

EXPOSE 8083

CMD ["python3", "-u", "dhcp_agent.py"]
