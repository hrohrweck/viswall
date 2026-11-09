#!/usr/bin/env python3
"""Viswall mail-service agent (minimal, Postgres-backed stack).

Exim and Dovecot read Postgres directly (see /opt/viswall/config + entrypoint.sh),
so this agent only exposes control/health endpoints. LLM email classification is a
follow-up enhancement wired via the api-gateway (see migration plan B3).
"""
import os
import secrets
import subprocess
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Viswall Mail Agent", version="2.0.0")

EXIM_CONF = "/etc/exim4/exim4.conf"
DKIM_STAGING_DIR = "/opt/viswall/dkim-staging"
EXIM_DKIM_DIR = "/etc/exim4/dkim"

INSTANCE_API_KEY = os.getenv("INSTANCE_API_KEY") or None


def _require_instance_key(
    x_instance_key: str | None = Header(default=None, alias="X-Instance-Key"),
) -> None:
    if INSTANCE_API_KEY is None:
        raise HTTPException(
            status_code=503,
            detail="INSTANCE_API_KEY not configured on agent; refusing mutations",
        )
    provided = (x_instance_key or "").encode("utf-8")
    if not secrets.compare_digest(provided, INSTANCE_API_KEY.encode("utf-8")):
        raise HTTPException(status_code=401, detail="invalid instance key")


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


class DkimInstallRequest(BaseModel):
    domain: str = Field(pattern=r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
    selector: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
    private_key_pem: str


@app.post("/dkim/install")
def dkim_install(req: DkimInstallRequest, _: None = Depends(_require_instance_key)):
    if (
        os.path.basename(req.domain) != req.domain
        or ".." in req.domain
        or req.domain in (".", "..")
    ):
        raise HTTPException(status_code=400, detail="invalid dkim domain")
    if os.path.basename(req.selector) != req.selector or req.selector in (".", ".."):
        raise HTTPException(status_code=400, detail="invalid dkim selector")
    # One key file per hosted domain — the exim template signs
    # $sender_address_domain when /etc/exim4/dkim/<domain>.private exists.
    paths = []
    for directory in (DKIM_STAGING_DIR, EXIM_DKIM_DIR):
        os.makedirs(directory, exist_ok=True)
        key_path = os.path.join(directory, f"{req.domain}.private")
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o400)
        with os.fdopen(fd, "w") as f:
            f.write(req.private_key_pem)
        _run(["chown", "Debian-exim:Debian-exim", key_path])  # best-effort
        paths.append(key_path)
    _run(["pkill", "-HUP", "-x", "exim4"])
    return {"status": "ok", "path": paths[0], "exim_path": paths[1], "reloaded": True}


def main():
    import uvicorn
    # The gateway reaches agents via the compose bridge over IPv4; a "::" bind is v6-only and unreachable.
    uvicorn.run(app, host=os.getenv("AGENT_HOST", "0.0.0.0"), port=int(os.getenv("AGENT_PORT", "8082")), log_level="info")


if __name__ == "__main__":
    main()
