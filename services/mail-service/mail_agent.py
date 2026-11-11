#!/usr/bin/env python3
"""Viswall mail-service agent (minimal, Postgres-backed stack).

Exim and Dovecot read Postgres directly (see /opt/viswall/config + entrypoint.sh),
so this agent only exposes control/health endpoints. LLM email classification is a
follow-up enhancement wired via the api-gateway (see migration plan B3).
"""
import json
import os
import re
import secrets
import subprocess
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(title="Viswall Mail Agent", version="2.0.0")

EXIM_CONF = "/etc/exim4/exim4.conf"
DKIM_STAGING_DIR = "/opt/viswall/dkim-staging"
EXIM_DKIM_DIR = "/etc/exim4/dkim"
MAIL_LOG_PATH = "/var/log/exim4/mainlog"
MAIL_LOG_ROTATED_PATH = "/var/log/exim4/mainlog.1"
MAIL_STATS_STATE_PATH = "/var/lib/viswall/mail-stats.json"

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


def _scan_log_lines(path, offset, counters):
    """Read `path` from byte `offset` to EOF, classifying each Exim mainlog
    line into `counters`. Returns the new EOF byte offset."""
    with open(path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            line = raw.decode("utf-8", "replace")
            low = line.lower()
            if " <= " in line:
                counters["received"] += 1
            if " => " in line:
                counters["delivered"] += 1
            if "rejected" in low and ("spam" in low or "score" in low):
                counters["rejected_spam"] += 1
            if "rejected" in low and ("malware" in low or "virus" in low or "clamd" in low):
                counters["rejected_virus"] += 1
        return fh.tell()


def _mail_counters():
    """Cumulative mail-activity counters tailed from the Exim mainlog.

    The read position is persisted in MAIL_STATS_STATE_PATH as
    {"inode": int, "offset": int, "counters": {"received": int,
    "delivered": int, "rejected_spam": int, "rejected_virus": int}},
    written atomically (temp file + rename), so counters survive log
    rotation and container restarts.

    Line classification (Exim mainlog format):
    - " <= " (case-sensitive substring) — message ARRIVAL → `received`.
      This counts ALL arrivals (inbound SMTP, outbound submissions, local
      bounces alike). It is NOT a true inbound/outbound split; the Metrics
      UI's inbound/outbound labels are an approximation.
    - " => " (case-sensitive substring) — completed DELIVERY → `delivered`
      (likewise all deliveries, not just outbound).
    - "rejected" (case-insensitive) AND ("spam" or "score") → `rejected_spam`.
    - "rejected" (case-insensitive) AND ("malware", "virus" or "clamd") →
      `rejected_virus`.
    - Any other line (deferrals, bounces, queue runs, "Completed") is not
      counted.

    NOTE: with the stock exim config (acl_check_data = `warn spam =
    nobody:true`, headers only) no log line can match the rejected_spam
    classifier, so rejected_spam stays 0 until a spam-deny ACL exists
    (a separate decision, not part of this agent).

    Rotation handling: when the mainlog inode differs from the stored one
    (logrotate, or a fresh anonymous /var/log/exim4 volume after a container
    recreate while the state file still holds the old inode), the rotated
    file's unread remainder is drained from the stored offset when mainlog.1
    is available; when mainlog.1 is missing or unreadable the remainder is
    discarded and the new file is read from offset 0 — the parser must never
    get stuck. When the inode matches but the stored offset exceeds the
    current file size, the offset is stale — a recycled inode on the
    recreated anonymous volume (fresh ext4 allocates inodes sequentially)
    or an in-place truncation — so the whole file is reread from offset 0;
    the collector's one-interval clamp keeps the rescan spike bounded. The
    first call without a state file reads the entire current log and stores
    it as the baseline (the collector's first delta is 0 because it has no
    previous snapshot, so the backlog never displays).

    Returns the counters dict (all zeros for an empty or fully-garbage log),
    or None on any error (log missing, permission denied) — /stats then
    reports "mail": null.
    """
    counters = {"received": 0, "delivered": 0, "rejected_spam": 0, "rejected_virus": 0}
    stored_inode = None
    stored_offset = 0
    try:
        try:
            with open(MAIL_STATS_STATE_PATH, encoding="utf-8") as fh:
                state = json.load(fh)
            stored_inode = int(state["inode"])
            stored_offset = int(state["offset"])
            for key in counters:
                counters[key] = int(state["counters"][key])
        except (OSError, ValueError, KeyError, TypeError):
            stored_inode = None  # no/corrupt state file → full first read

        st = os.stat(MAIL_LOG_PATH)
        if stored_inode == st.st_ino and stored_offset > st.st_size:
            stored_offset = 0  # recycled inode / in-place truncation: stale offset
        if stored_inode == st.st_ino:
            offset = _scan_log_lines(MAIL_LOG_PATH, stored_offset, counters)
        else:
            if stored_inode is not None:
                try:
                    _scan_log_lines(MAIL_LOG_ROTATED_PATH, stored_offset, counters)
                except OSError:
                    pass  # mainlog.1 missing/unreadable → skip the drain
            offset = _scan_log_lines(MAIL_LOG_PATH, 0, counters)

        os.makedirs(os.path.dirname(MAIL_STATS_STATE_PATH), exist_ok=True)
        tmp_path = MAIL_STATS_STATE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump({"inode": st.st_ino, "offset": offset, "counters": counters}, fh)
        os.replace(tmp_path, MAIL_STATS_STATE_PATH)
        return dict(counters)
    except Exception:
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
    counters = _mail_counters()
    return {
        "queue_length": _queue_length(),
        "mail": counters,  # {"received": int, "delivered": int, "rejected_spam": int, "rejected_virus": int} or None
    }


_LOG_TS_PREFIX = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def _normalize_time_bound(value, is_until):
    """Normalize a since/until bound for lexicographic comparison against the
    zero-padded 19-char exim timestamp prefix ("YYYY-MM-DD HH:MM:SS").

    Accepts "YYYY-MM-DD HH:MM[:SS]" or the datetime-local "T" separator.
    A 16-char bound (minute precision) is padded to a whole minute:
    ":00" for since, ":59" for until — both bounds stay inclusive.
    """
    normalized = value.replace("T", " ")
    if len(normalized) == 16:
        normalized += ":59" if is_until else ":00"
    return normalized


@app.get("/logs")
def get_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=200),
    q: str | None = None,
    domain: str | None = None,
    mail_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    _: None = Depends(_require_instance_key),
):
    """Filtered, paginated Exim mainlog lines for log investigation.

    Reads MAIL_LOG_ROTATED_PATH first (when present and readable), then
    MAIL_LOG_PATH — the oldest→newest concatenation. The matched set is
    then REVERSED, so the returned page order is newest→oldest
    (user-directed change superseding the original oldest-first default):
    offset 0 is the NEWEST page, deeper offsets walk backwards in time,
    and the last page holds the oldest line. Active filters apply
    with AND:
    - q: case-insensitive substring on the whole line
    - domain: case-insensitive substring (matches user@domain and HELO strings)
    - mail_id: substring (exim queue ids)
    - since/until: "YYYY-MM-DD HH:MM[:SS]" or "YYYY-MM-DDTHH:MM[:SS]",
      agent-local time, both bounds INCLUSIVE. The exim timestamp is a
      zero-padded fixed-width prefix, so the bounds are normalized (T→space;
      a 16-char bound is padded :00 for since / :59 for until) and compared
      LEXICOGRAPHICALLY against line[:19] — never datetime.strptime per line
      (which would cost ~1 s at today's log size). Lines shorter than 19
      chars or without a timestamp-shaped "YYYY-MM-DD " prefix are excluded
      only while a time filter is active.

    `limit` is clamped after parsing to 1..500 (never a 422); the page is
    sliced AFTER filtering and the newest→oldest reversal, and `next_offset`
    is `offset + limit` only when more matched lines follow, else None (the
    end sentinel the gateway schema and the UI infinite query key on) —
    pagination semantics unchanged.

    Rotation-drift tolerance: offsets are computed per request against the
    CURRENT concatenation; if logrotate rotates between two client requests,
    offsets may shift and a page can repeat or skip lines — accepted, this
    endpoint is stateless by design.

    Performance: full scan of the readable sources per request (~70k lines /
    8.8 MB today ≈ tens of ms; p95 < 300 ms verified in the Task 5 deploy lane).

    Missing or unreadable log files yield an empty 200, never a 500.
    """
    limit = min(500, max(1, limit))
    since_bound = _normalize_time_bound(since, False) if since is not None else None
    until_bound = _normalize_time_bound(until, True) if until is not None else None
    q_lower = q.lower() if q is not None else None
    domain_lower = domain.lower() if domain is not None else None

    matched = []
    source_files = []
    for path in (MAIL_LOG_ROTATED_PATH, MAIL_LOG_PATH):
        try:
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError:
            continue
        source_files.append(os.path.basename(path))
        with fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if since_bound is not None or until_bound is not None:
                    if _LOG_TS_PREFIX.match(line) is None:
                        continue
                    stamp = line[:19]
                    if since_bound is not None and stamp < since_bound:
                        continue
                    if until_bound is not None and stamp > until_bound:
                        continue
                if q_lower is not None or domain_lower is not None:
                    low = line.lower()
                    if q_lower is not None and q_lower not in low:
                        continue
                    if domain_lower is not None and domain_lower not in low:
                        continue
                if mail_id is not None and mail_id not in line:
                    continue
                matched.append(line)

    matched.reverse()
    total_matched = len(matched)
    next_offset = offset + limit if total_matched > offset + limit else None
    return {
        "lines": matched[offset : offset + limit],
        "total_matched": total_matched,
        "next_offset": next_offset,
        "source_files": source_files,
    }


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
