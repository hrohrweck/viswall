FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bind9 \
    bind9-utils \
    dnsutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    fastapi \
    uvicorn \
    pydantic

COPY services/dns-service/dns_agent.py /opt/viswall/

WORKDIR /opt/viswall

EXPOSE 8082

CMD ["python3", "-u", "dns_agent.py"]
