# Continuous Deployment — viswall.webmasters.co.at

Every merge to `main` that passes CI is built and deployed automatically to the production server `viswall.webmasters.co.at`. CI/CD runs on the **self-hosted Jenkins** at `http://10.80.2.251:8081` (the `enterprise` host), mirroring the vidForge setup — see `ci/jenkins/README.md`. GitHub remains the source/PR host only (plus the lightweight `security.yml` gitleaks scan); the former GitHub Actions workflows (`ci.yml`, `deploy.yml`, `sdk.yml`) are retired.

## How it works

```
GitHub webhook (push / pull_request / issue_comment)
 └─ https://viswall.webmasters.co.at/jenkins-hook/…   (host nginx on boseman → Jenkins)
     └─ Jenkins generic-webhook-trigger (token: viswall-gwt-token credential)
         ├─ viswall-ci      (agent 'build')
         │    backend tests (Postgres/Redis sidecars), frontend, OpenAPI/SDK/CLI
         │    PRs → "jenkins-ci" commit status; green main → trigger release
         ├─ viswall-release (agent 'build')
         │    buildx builds api-gateway, web-ui, sogo, dns-service
         │    tags: sha-<short7> and main → ghcr.io/hrohrweck/viswall/*
         │    (registry :buildcache; Trivy scan was retired with GH Actions)
         └─ viswall-deploy  (agent 'build', serialized)
              SSH → viswall-deploy@viswall.webmasters.co.at
                pin checkout → ghcr login → pre-pull (3 retries)
                ./scripts/deploy.sh <tag> <sha>
                  (pg_dump backup → compose pull/up incl. mail profile
                   → health gates → auto-rollback)

viswall-approve: "/approve" comment by the PR author → vidforge-bot posts
the approving review (the "Protect main" ruleset requires 1 approval).
```

- Deploys are serialized (`disableConcurrentBuilds` on viswall-deploy) and never cancel mid-flight.
- The release/deploy chain only fires from a **green main CI build** (same gate the `workflow_run` trigger provided under GitHub Actions).
- Webhook payloads for the two repos are isolated by token: viswall jobs use the `viswall-gwt-token` credential, vidforge jobs keep their own.

## What is deployed

`deployments/docker/docker-compose.prod.yml` overrides the four custom images that the default compose profile runs:

| Image | Dockerfile | Notes |
|---|---|---|
| `ghcr.io/hrohrweck/viswall/api-gateway` | `services/api-gateway/Dockerfile` | runs DB migrations on startup (`init_db()` → `alembic upgrade head`) |
| `ghcr.io/hrohrweck/viswall/web-ui` | `web-ui/Dockerfile` | nginx serving the Vite build |
| `ghcr.io/hrohrweck/viswall/sogo` | `services/sogo-service/Dockerfile` | |
| `ghcr.io/hrohrweck/viswall/dns-service` | `services/dns-service/Dockerfile` | authoritative DNS on 46.4.63.216:53 |

`nginx` (profile `disabled`) is intentionally **not** prebuilt — TLS is terminated by the existing host nginx. `mail-service` (profile `mail`) **is enabled in production** (Exim/Dovecot carry live mail) and builds locally on the server during each deploy; its DKIM keys live in `/opt/viswall/dkim` (untracked, preserved across deploys).

Third-party images (postgres, redis, prometheus, grafana, ollama) are pulled directly by compose. Data lives in named volumes and survives every deploy.

## Production setup (as deployed 2026-10)

| Component | Value |
|---|---|
| Server | `viswall.webmasters.co.at` (Hetzner `46.4.63.216`, hostname `boseman`) — also hosts vidForge and other stacks |
| Checkout | `/opt/viswall` (git clone, owned by `viswall-deploy`; `/opt/viswall/dkim` holds the DKIM keys — untracked and preserved across deploys) |
| Compose env | `/opt/viswall/deployments/docker/.env` (0600, copied from the retired pre-CD deployment at `/data/docker/persistent/viswall/viswall/`) |
| Deploy SSH user | `viswall-deploy` (member of `docker`) |
| Jenkins | `http://10.80.2.251:8081` on `enterprise` (docker compose at `/naspool/CI/`, home `/naspool/CI/jenkins_home`); jobs `viswall-ci`, `viswall-release`, `viswall-deploy`, `viswall-approve` — "Pipeline script from SCM", branch `**/main` |
| Jenkins credentials | `viswall-gwt-token` (webhook token), `viswall-deploy-ssh` (deploy SSH key), `vidforge-github-pat` (GitHub PAT of `vidforge-bot`, shared with the vidforge jobs: commit statuses, PR approvals, GHCR push/pull) |
| Webhook | repo hook (push, pull_request, issue_comment) → `https://viswall.webmasters.co.at/jenkins-hook/generic-webhook-trigger/invoke?token=…`; relayed by the `/jenkins-hook/` location in `viswall.conf` on the host nginx → `http://10.80.2.251:8081/` |
| Git access on server | read-only deploy key `deploy: boseman/viswall.webmasters.co.at` → `/home/viswall-deploy/.ssh/viswall_deploy_key` |

The pre-CD deployment at `/data/docker/persistent/viswall/viswall/` is retired: same compose project name (`name: viswall` in the compose file), so `/opt/viswall` adopts its containers and named volumes (`viswall_postgres_data`, …). Do not run `docker compose up` from the old directory again.

### Rebuilding the setup from scratch (disaster recovery)

1. **Jenkins jobs**: create `viswall-ci`, `viswall-release`, `viswall-deploy`, `viswall-approve` as "Pipeline script from SCM" jobs pointing at `https://github.com/hrohrweck/viswall.git` (branch `**/main`, script paths per `ci/jenkins/README.md`). The `viswall-gwt-token` and `viswall-deploy-ssh` credentials must exist first (credentials store, script console).
2. **Webhook relay**: the `/jenkins-hook/` location must exist in the `viswall.conf` server block of the host nginx on boseman (`/data/docker/persistent/nginx/config/conf.d/`), then `nginx -s reload`.
3. **Server**: create `viswall-deploy` (docker group), clone the repo to `/opt/viswall` with a read-only deploy key, restore `.env` from backups, install the Jenkins deploy public key into `~viswall-deploy/.ssh/authorized_keys`.
4. **Webhook**: add the repo hook (push, pull_request, issue_comment) with the `viswall-gwt-token` secret in the URL.
5. **First deploy**: run `viswall-release` manually (empty `GIT_SHA` = main HEAD), or merge anything to main.

## What a deploy run does (`scripts/deploy.sh`)

1. **Pin checkout** — `git fetch origin main` + `git reset --hard <sha>` so the bind-mounted `shared/`, compose files, and the script itself match the built images.
2. **DB backup** — `pg_dump` into `deployments/docker/backups/` (gzipped, last 10 kept) *before* api-gateway startup runs migrations. Skipped if postgres is not running.
3. **Pull & apply** — `VISWALL_TAG=<tag> docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && up --profile mail -d --remove-orphans` (the `mail` profile is active in production; mail-service builds locally). Unchanged services (postgres, redis, …) are not restarted.
4. **Health gates** (300 s each):
   - in-container `GET http://127.0.0.1:8000/health` on api-gateway;
   - public probe of `PUBLIC_HEALTH_URL` (default `https://viswall.webmasters.co.at/`).
5. **Success** — writes the tag to `deployments/docker/.last-good-tag`, prunes dangling images.
   **Failure** — rolls the stack back to `.last-good-tag` and exits 1. On the very first deploy (no known-good tag) the current state is left in place for manual inspection rather than taking a live site down.

## Rollback & manual operations

```bash
# Redeploy an older tag (list available tags on the GHCR package page):
ssh viswall-deploy@viswall.webmasters.co.at
cd /opt/viswall/deployments/docker
VISWALL_TAG=sha-abc1234 docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
VISWALL_TAG=sha-abc1234 docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile mail up -d --remove-orphans

# Trigger a fresh deploy of current main without a merge:
#   Jenkins → viswall-release → Build with Parameters (GIT_SHA empty, SKIP_DEPLOY unchecked)
```

Database dumps are **not** restored automatically. The latest dumps live in
`deployments/docker/backups/`; restore manually with
`gunzip -c <dump>.sql.gz | docker compose exec -T postgres psql -U viswall viswall`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Jenkins job stuck in *Queue* | 'build' agent offline — check `docker ps | grep jenkins` and node status on `http://10.80.2.251:8081/computer/`. |
| Merge produces no Jenkins build | Webhook delivery failing — GitHub repo → Settings → Webhooks → recent deliveries; relay path must exist in `viswall.conf` and the `viswall-gwt-token` secret must match the token in the webhook URL. |
| vidforge jobs start on viswall events (or vice versa) | Token leak/mixup — each repo's webhook URL must carry its own GWT token; jobs match by `tokenCredentialId`. |
| `docker pull … denied` in viswall-deploy | GHCR credential issue — `vidforge-github-pat` must have packages write for `ghcr.io/hrohrweck/viswall/*`; check the `docker login` output in the deploy log. |
| Health gate fails, rollback runs | Check `docker compose logs api-gateway` (often a migration or bad env in `.env`) and whether the public URL responds. |
| `git reset --hard` fails in deploy | Ownership/permission on `/opt/viswall` (must be writable by `viswall-deploy`) or a fetch-auth failure of the server's deploy key. |
| PR shows no `jenkins-ci` status | The PR head was pushed before the Jenkins setup existed, or the commit-status POST failed (PAT scope). Re-run `viswall-ci` manually with the event vars left empty and `CI_SHA` handling via checkout. |
| DNS or mail regressions | `dns-service` publishes authoritative DNS on 46.4.63.216:53 — a failed deploy rolls back automatically; verify with `dig @46.4.63.216 <zone> SOA`. |
