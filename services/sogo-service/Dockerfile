# --- Stage 1: build the bind() LD_PRELOAD shim ---
FROM debian:bookworm-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY services/sogo-service/bindfix.c /tmp/bindfix.c
RUN gcc -shared -fPIC -O2 -o /tmp/bindfix.so /tmp/bindfix.c -ldl

# --- Stage 2: final image ---
FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# SOGo + memcached for sessions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    sogo \
    memcached \
    gosu \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# bindfix.so: works around gnustep-base 1.28.0 sin_family corruption
COPY --from=builder /tmp/bindfix.so /usr/lib/bindfix.so

COPY services/sogo-service/sogo.conf.template /etc/sogo/sogo.conf.template
COPY services/sogo-service/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 20000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sogod", "-WONoDetach", "YES", "-WOPidFile", "/var/run/sogo/sogo.pid"]
