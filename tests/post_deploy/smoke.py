#!/usr/bin/env python3
"""Post-deploy regression suite for Viswall.

Runs against a live deployment (by default the public URL through nginx) and
checks that core functionality survived the release. Strictly read-only:
the only non-GET request is the single login that mints the bearer token;
its only side effect is `last_login` on the dedicated smoke user.

Zero third-party dependencies (stdlib only) so it can run on the prod host,
inside a container, or from a laptop.

Exit codes:
    0  all checks passed (skipped checks don't fail the run)
    1  at least one check failed  -> scripts/deploy.sh rolls back
    2  configuration error (bad SMOKE_BASE_URL, missing credentials)

Configuration (environment variables):
    SMOKE_BASE_URL     base URL, absolute http(s) only (default: https://viswall.webmasters.co.at)
    SMOKE_USERNAME     login for the smoke user (required)
    SMOKE_PASSWORD     password for the smoke user (required)
    SMOKE_TIMEOUT      per-request timeout in seconds (default: 15)
    SMOKE_API_ONLY     "1" skips the web-ui check, for api-only targets (default: 0)

TLS is always verified. For dev stacks with a self-signed CA, point
SSL_CERT_FILE at the CA bundle instead of disabling verification.

Manual run:
    SMOKE_BASE_URL=https://viswall.webmasters.co.at \
    SMOKE_USERNAME=viswall-smoke SMOKE_PASSWORD=... \
    python3 tests/post_deploy/smoke.py
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

BASE_URL = os.environ.get("SMOKE_BASE_URL", "https://viswall.webmasters.co.at").rstrip("/")
USERNAME = os.environ.get("SMOKE_USERNAME", "")
PASSWORD = os.environ.get("SMOKE_PASSWORD", "")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "15"))
API_ONLY = os.environ.get("SMOKE_API_ONLY", "") not in ("", "0", "false")

_parsed_base = urlparse(BASE_URL)
if _parsed_base.scheme not in ("https", "http") or not _parsed_base.hostname:
    print("FATAL: SMOKE_BASE_URL must be an absolute http(s) URL, got: %r" % BASE_URL)
    sys.exit(2)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Treat redirects as terminal responses.

    The suite sends a bearer token; silently following a redirect (urllib's
    default) could replay it against a different origin than the one the
    operator configured. Core endpoints must answer directly anyway, so a
    3xx surfaces as a check failure.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))

_results = []


def check(name, ok, detail=""):
    """Record one check result. ok may be True, False or None (skipped)."""
    _results.append((name, ok, detail))
    label = {True: "PASS", False: "FAIL", None: "SKIP"}[ok]
    line = "[%s] %s" % (label, name)
    if detail:
        line += " — " + detail
    print(line)
    return ok


def http(method, path, token=None, body=None, expect_json=True):
    """Issue one request against BASE_URL; returns (status, parsed_json_or_raw_bytes)."""
    if not path.startswith("/"):
        raise ValueError("path must be root-relative, got: %r" % path)
    url = BASE_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with _opener.open(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            status = resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    if expect_json:
        try:
            return status, json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return status, raw
    return status, raw


def c_health():
    """GET /health — api-gateway up, DB reachable."""
    status, body = http("GET", "/health")
    ok = status == 200 and isinstance(body, dict) and body.get("status") == "healthy"
    check("api /health", ok, "HTTP %s" % status)
    return ok


def c_web_ui():
    """GET / — nginx serves the React SPA."""
    if API_ONLY:
        return check("web-ui served at /", None, "SMOKE_API_ONLY=1")
    status, body = http("GET", "/", expect_json=False)
    ok = status == 200 and (b'<div id="root"' in body or b"<html" in body)
    check("web-ui served at /", ok, "HTTP %s" % status)
    return ok


def c_openapi():
    """GET /api/openapi.json — API contract is exposed."""
    status, body = http("GET", "/api/openapi.json")
    ok = status == 200 and isinstance(body, dict) and isinstance(body.get("paths"), dict)
    check("openapi spec at /api/openapi.json", ok, "HTTP %s" % status)
    return ok


def c_api_info():
    """GET /api/v1/ — api_info endpoint answers."""
    status, body = http("GET", "/api/v1/")
    ok = status == 200 and isinstance(body, dict) and "Viswall" in str(body.get("name", ""))
    check("api info at /api/v1/", ok, "HTTP %s" % status)
    return ok


def c_auth_negative():
    """GET /api/v1/instances without a token must be rejected (401/403)."""
    status, _ = http("GET", "/api/v1/instances")
    ok = status in (401, 403)
    check("unauthenticated request rejected", ok, "HTTP %s" % status)
    return ok


def c_login(token_box):
    """POST /api/v1/auth/login — the only write-ish call (smoke user's last_login)."""
    if not USERNAME or not PASSWORD:
        return check("login %s" % USERNAME, False, "SMOKE_USERNAME/SMOKE_PASSWORD not set")
    status, body = http("POST", "/api/v1/auth/login", body={"username": USERNAME, "password": PASSWORD})
    ok = status == 200 and isinstance(body, dict) and bool(body.get("access_token"))
    check("login %s" % USERNAME, ok, "HTTP %s" % status)
    if ok:
        token_box["token"] = body["access_token"]
    return ok


def c_me(token_box):
    """GET /api/v1/auth/me — token round-trips, JWT claims decode."""
    token = token_box.get("token")
    if not token:
        return check("/auth/me returns smoke user", None, "no token (login failed)")
    status, body = http("GET", "/api/v1/auth/me", token=token)
    ok = status == 200 and isinstance(body, dict) and body.get("username") == USERNAME
    check("/auth/me returns smoke user", ok, "HTTP %s" % status)
    return ok


def c_instances(token_box):
    """GET /api/v1/instances — core listing works; returns first instance id."""
    token = token_box.get("token")
    if not token:
        check("list instances", None, "no token (login failed)")
        return None
    status, body = http("GET", "/api/v1/instances", token=token)
    ok = status == 200 and isinstance(body, list)
    check("list instances", ok, "HTTP %s, %s items" % (status, len(body) if isinstance(body, list) else "?"))
    return body[0].get("id") if ok and body and isinstance(body[0], dict) else None


def _instance_scoped(name, path, expect, token_box, instance_id):
    """GET one instance-scoped read endpoint (DB-backed, safe on empty tables)."""
    token = token_box.get("token")
    if not token:
        return check(name, None, "no token (login failed)")
    if instance_id is None:
        return check(name, None, "no instances configured")
    status, body = http("GET", path % instance_id, token=token)
    ok = status == 200 and isinstance(body, expect)
    check(name, ok, "HTTP %s" % status)
    return ok


def c_users(token_box):
    """GET /api/v1/users — admin-only listing."""
    token = token_box.get("token")
    if not token:
        return check("list users (admin)", None, "no token (login failed)")
    status, body = http("GET", "/api/v1/users", token=token)
    ok = status == 200 and isinstance(body, list)
    check("list users (admin)", ok, "HTTP %s" % status)
    return ok


def c_audit(token_box):
    """GET /api/v1/audit — admin-only, audit trail queryable."""
    token = token_box.get("token")
    if not token:
        return check("query audit log (admin)", None, "no token (login failed)")
    status, body = http("GET", "/api/v1/audit?limit=5", token=token)
    ok = status == 200 and isinstance(body, list)
    check("query audit log (admin)", ok, "HTTP %s" % status)
    return ok


def c_metrics_overview(token_box):
    """GET /api/v1/metrics/overview — dashboard aggregates."""
    token = token_box.get("token")
    if not token:
        return check("metrics overview", None, "no token (login failed)")
    status, body = http("GET", "/api/v1/metrics/overview", token=token)
    ok = status == 200 and isinstance(body, dict)
    check("metrics overview", ok, "HTTP %s" % status)
    return ok


def c_prometheus():
    """GET /metrics — Prometheus scrape endpoint exposed."""
    status, body = http("GET", "/metrics", expect_json=False)
    ok = status == 200 and len(body) > 0
    check("prometheus /metrics", ok, "HTTP %s" % status)
    return ok


def main():
    print("Viswall post-deploy regression suite")
    print("Target: %s" % BASE_URL)
    print("-" * 60)

    token_box = {}

    c_health()
    c_web_ui()
    c_openapi()
    c_api_info()
    c_auth_negative()

    c_login(token_box)
    c_me(token_box)

    first_id = c_instances(token_box)

    # Instance-scoped reads (all DB-backed, tolerate empty tables). Only
    # meaningful if the instance listing itself worked.
    if first_id is not None or token_box.get("token"):
        _instance_scoped("firewall rules of first instance",
                         "/api/v1/firewall/rules/%s", list, token_box, first_id)
        _instance_scoped("mail domains of first instance",
                         "/api/v1/mail/domains/%s", list, token_box, first_id)
        _instance_scoped("dns servers of first instance",
                         "/api/v1/dns/servers/%s", list, token_box, first_id)
        _instance_scoped("vpn servers of first instance",
                         "/api/v1/vpn/servers/%s", list, token_box, first_id)
        _instance_scoped("dhcp servers of first instance",
                         "/api/v1/dhcp/servers/%s", list, token_box, first_id)
        _instance_scoped("metrics dashboard of first instance",
                         "/api/v1/metrics/dashboard/%s", dict, token_box, first_id)
    else:
        check("instance-scoped reads", None, "login failed — skipping")

    c_users(token_box)
    c_audit(token_box)
    c_metrics_overview(token_box)
    c_prometheus()

    print("-" * 60)
    failed = [r for r in _results if r[1] is False]
    skipped = [r for r in _results if r[1] is None]
    passed = len(_results) - len(failed) - len(skipped)
    print("Summary: %d passed, %d failed, %d skipped" % (passed, len(failed), len(skipped)))

    if failed:
        print("FAILED checks:")
        for name, _, detail in failed:
            print("  - %s (%s)" % (name, detail))
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
