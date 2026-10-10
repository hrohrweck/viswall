# Post-deploy regression suite

Read-only smoke tests that `scripts/deploy.sh` runs against the live stack
after every deploy, between the health gates and the `.last-good-tag` update:

1. Health gates pass (api `/health`, public URL).
2. **This suite runs** (`tests/post_deploy/smoke.py`).
3. On success, the new tag is recorded as known-good.
4. On failure, `deploy.sh` rolls the stack back to the previous known-good
   tag and exits `3`; the remote wrapper does **not** retry, so the bad
   version never goes live again. The Jenkins `verify` stage then fails
   because the server did not converge on the new tag.

## What is tested

All checks are GET requests against the deployed stack through nginx —
no business data is created, modified, or deleted. The single exception is
one `POST /api/v1/auth/login` as the dedicated smoke user, whose only side
effect is `last_login` on that user.

| Check | Endpoint |
|-------|----------|
| API up, DB reachable | `GET /health` |
| Web UI served | `GET /` |
| API contract exposed | `GET /api/openapi.json`, `GET /api/v1/` |
| Auth rejects anonymous requests | `GET /api/v1/instances` without token → 401/403 |
| Login + JWT round-trip | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Core listings | instances, users, audit log, metrics overview |
| Instance-scoped reads (first instance) | firewall rules, mail domains, DNS/VPN/DHCP servers, metrics dashboard |
| Prometheus scrape endpoint | `GET /metrics` |

All instance-scoped endpoints are DB-backed and tolerate empty tables, so
the suite passes on a freshly provisioned stack. Redirects are treated as
failures and TLS is always verified (for a self-signed dev CA, point
`SSL_CERT_FILE` at the bundle).

## One-time setup

The suite needs a dedicated local user. Until credentials are configured it
is **skipped** with a warning (deploys proceed unguarded) — set this up once:

1. Create the user in the Viswall UI (**Users** page), e.g.
   `viswall-smoke` with a long random password (`openssl rand -base64 24`).
   Role `admin` is required for the users/audit checks; `superadmin`
   additionally sees all instances, giving the widest coverage.
2. On the prod server, add to `/opt/viswall/deployments/docker/.env`:

   ```
   SMOKE_USERNAME=viswall-smoke
   SMOKE_PASSWORD=<the generated password>
   ```

   One `KEY=value` per line, values unquoted. Environment variables of the
   same name take precedence (useful for manual runs).

## Running manually

Against any environment:

```bash
SMOKE_BASE_URL=https://viswall.webmasters.co.at \
SMOKE_USERNAME=viswall-smoke SMOKE_PASSWORD=... \
python3 tests/post_deploy/smoke.py
```

API-only target (e.g. `http://localhost:8000`, no nginx in front):
add `SMOKE_API_ONLY=1`.

Exit codes: `0` pass, `1` checks failed, `2` configuration error.

## Adding checks

Add a `c_*` function that uses `http()` and `check()`, and call it from
`main()`. Keep the suite read-only: anything that creates, updates, or
deletes business data has no place here — the suite gates production
deploys and must be safe to run against live state at any time.
