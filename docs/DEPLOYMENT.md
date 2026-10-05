# Continuous Deployment — viswall.webmasters.co.at

Every merge to `main` that passes CI is built and deployed automatically to the production server `viswall.webmasters.co.at`. Builds and deploys run on the self-hosted GitHub Actions runner at `10.80.2.251` (label `viswall`), following the same pattern as the vidForge project.

## How it works

```
PR merged to main
 └─ .github/workflows/ci.yml   "Viswall CI/CD"        (GitHub-hosted runners)
     │   test-backend / test-frontend / test-integration
     ▼ on success
   .github/workflows/deploy.yml "Deploy"              (self-hosted runner, 10.80.2.251)
     ├─ job images
     │    builds api-gateway, web-ui, sogo, dns-service
     │    tags: sha-<short7> and main
     │    pushes to ghcr.io/hrohrweck/viswall/*
     │    runs a Trivy filesystem scan (results → GitHub Security tab)
     └─ job deploy  (environment: production)
          SSH → viswall.webmasters.co.at
            docker login ghcr.io (workflow GITHUB_TOKEN)
            ./scripts/deploy.sh <tag> <sha>
```

- Deploys are serialized by the `viswall-deploy` concurrency group and never cancel mid-flight.
- The `images` job only fires when CI **succeeded** (`workflow_run` gate) or on manual `workflow_dispatch`.
- PR jobs never run on the self-hosted runner — only events on `main` reach it.

## What is deployed

`deployments/docker/docker-compose.prod.yml` overrides the four custom images that the default compose profile runs:

| Image | Dockerfile | Notes |
|---|---|---|
| `ghcr.io/hrohrweck/viswall/api-gateway` | `services/api-gateway/Dockerfile` | runs DB migrations on startup (`init_db()` → `alembic upgrade head`) |
| `ghcr.io/hrohrweck/viswall/web-ui` | `web-ui/Dockerfile` | nginx serving the Vite build |
| `ghcr.io/hrohrweck/viswall/sogo` | `services/sogo-service/Dockerfile` | |
| `ghcr.io/hrohrweck/viswall/dns-service` | `services/dns-service/Dockerfile` | authoritative DNS on 46.4.63.216:53 |

`nginx` (profile `disabled`) and `mail-service` (profile `mail`) are intentionally **not** prebuilt — TLS is terminated by the existing host nginx, and if either profile is ever enabled on the server it keeps building locally.

Third-party images (postgres, redis, prometheus, grafana, ollama) are pulled directly by compose. Data lives in named volumes and survives every deploy.

## Production setup (as deployed 2026-10-05)

| Component | Value |
|---|---|
| Server | `viswall.webmasters.co.at` (Hetzner `46.4.63.216`, hostname `boseman`) — also hosts vidForge and other stacks |
| Checkout | `/opt/viswall` (git clone, owned by `viswall-deploy`; pre-existing `/opt/viswall/dkim` dir is untracked and preserved) |
| Compose env | `/opt/viswall/deployments/docker/.env` (0600, copied from the retired pre-CD deployment at `/data/docker/persistent/exim4/viswall/`) |
| Deploy SSH user | `viswall-deploy` (member of `docker`) |
| Self-hosted runner | `enterprise-viswall-1` on `10.80.2.251` — docker compose service `ghar-viswall-1` in the `gh-runners` project (`/naspool/home/sysop/source/private/build/gh-runners/docker-compose.yml`), labels `self-hosted,linux,x64,viswall`, docker socket mounted + `group_add: docker` |
| Repo secrets | `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `SSH_FINGERPRINT` (ED25519 host key of the server) |
| GitHub environment | `production` (no protection rules — add reviewers here if manual approval is wanted) |
| Git access on server | read-only deploy key `deploy: boseman/viswall.webmasters.co.at` → `/home/viswall-deploy/.ssh/viswall_deploy_key` |

The pre-CD deployment at `/data/docker/persistent/exim4/viswall/` is retired: same compose project name (`name: viswall` in the compose file), so `/opt/viswall` adopts its containers and named volumes (`viswall_postgres_data`, …) on the first deploy. Do not run `docker compose up` from the old directory again.

### Rebuilding the setup from scratch (disaster recovery)

1. **Runner**: on 10.80.2.251 add a `ghar-viswall-1` service to the `gh-runners` compose project (copy the `ghar-vidForge-1` service, change `REPO_URL`/`RUNNER_NAME`/`RUNNER_LABELS`), then `docker compose up -d ghar-viswall-1`. The fleet's shared PAT in `.env` mints the registration token per start (runners are ephemeral — one job per container incarnation).
2. **Server**: create `viswall-deploy` (docker group), clone the repo to `/opt/viswall` with a read-only deploy key, restore `.env` from backups, install the Actions public key into `~viswall-deploy/.ssh/authorized_keys`.
3. **Secrets**: rotate the keypair, then `gh secret set SSH_HOST/SSH_USER/SSH_PRIVATE_KEY/SSH_FINGERPRINT -R hrohrweck/viswall …` (fingerprint: `ssh-keyscan -t ed25519 <host> | ssh-keygen -lf -`).
4. **First deploy**: Actions → Deploy → Run workflow.

## What a deploy run does (`scripts/deploy.sh`)

1. **Pin checkout** — `git fetch origin main` + `git reset --hard <sha>` so the bind-mounted `shared/`, compose files, and the script itself match the built images.
2. **DB backup** — `pg_dump` into `deployments/docker/backups/` (gzipped, last 10 kept) *before* api-gateway startup runs migrations. Skipped if postgres is not running.
3. **Pull & apply** — `VISWALL_TAG=<tag> docker compose -f docker-compose.yml -f docker-compose.prod.yml pull && up -d --remove-orphans`. Unchanged services (postgres, redis, …) are not restarted.
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
VISWALL_TAG=sha-abc1234 docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans

# Trigger a fresh deploy of current main without a merge:
#   Actions → Deploy → Run workflow
```

Database dumps are **not** restored automatically. The latest dumps live in
`deployments/docker/backups/`; restore manually with
`gunzip -c <dump>.sql.gz | docker compose exec -T postgres psql -U viswall viswall`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Deploy job stuck in *Queued* | Self-hosted runner offline — check `sudo ./svc.sh status` on 10.80.2.251, or the runner's label no longer matches `[self-hosted, viswall]`. |
| `docker compose pull failed` on server | GHCR login failed — the workflow token must have `packages: write` (set at workflow level); check the `docker login` step output in the SSH script. |
| Health gate fails, rollback runs | Check `docker compose logs api-gateway` (often a migration or bad env in `.env`) and whether the public URL responds. |
| `git reset --hard` fails in deploy | Ownership/permission on `/opt/viswall` (must be writable by `SSH_USER`) or a fetch-auth failure of the server's deploy key. |
| Deploy workflow never fires after merge | `workflow_run` only triggers when `deploy.yml` exists on `main` and CI's *name* matches `Viswall CI/CD`. Use `workflow_dispatch` as a fallback. |
| DNS or mail regressions | `dns-service` publishes authoritative DNS on 46.4.63.216:53 — a failed deploy rolls back automatically; verify with `dig @46.4.63.216 <zone> SOA`. |
