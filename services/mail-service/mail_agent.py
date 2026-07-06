#!/usr/bin/env python3
"""Viswall mail-service agent (minimal, Postgres-backed stack).

Exim and Dovecot read Postgres directly (see /opt/viswall/config + entrypoint.sh),
so this agent only exposes control/health endpoints. LLM email classification is a
follow-up enhancement wired via the api-gateway (see migration plan B3).
"""
import os
import subprocess
from fastapi import FastAPI

app = FastAPI(title="Viswall Mail Agent", version="2.0.0")

EXIM_CONF = "/etc/exim4/exim4.conf"


def _run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # pragma: no cover
        return 1, str(e)


def _queue_length():
    rc, out = _run(["exim4", "-C", EXIM_CONF, "-bpc"])
    try:
        return int(out) if rc == 0 else None
    except ValueError:
        return None


@app.get("/health")
def health():
    checks = {
        "exim_config": _run(["exim4", "-C", EXIM_CONF, "-bV"])[0] == 0,
        "dovecot_config": _run(["doveconf", "-n"])[0] == 0,
    }
    status = "ok" if all(checks.values()) else "degraded"
    return {"status": status, "checks": checks, "queue_length": _queue_length()}


@app.get("/stats")
def stats():
    return {"queue_length": _queue_length()}


@app.post("/reload")
def reload():
    rc, out = _run(["exim4", "-C", EXIM_CONF, "-bV"])
    if rc != 0:
        return {"reloaded": False, "error": "exim config invalid", "detail": out}
    _run(["pkill", "-HUP", "-x", "exim4"])
    _run(["doveadm", "reload"])
    return {"reloaded": True}


@app.post("/classify")
def classify():
    # LLM classification is provided via the api-gateway integration (follow-up, plan B3).
    return {"enabled": False, "detail": "LLM classification not configured in this build"}


def main():
    import uvicorn
    uvicorn.run(app, host="::", port=int(os.getenv("AGENT_PORT", "8082")), log_level="info")


if __name__ == "__main__":
    main()
