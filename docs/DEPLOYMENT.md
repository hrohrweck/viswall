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

## One-time setup

### 1. Register the self-hosted runner on 10.80.2.251

The viswall repo needs its own runner registration (runners are scoped per repo/org; vidForge's runner is not visible to this repo). A second registration can run alongside the vidForge one on the same host:

1. GitHub → `hrohrweck/viswall` → Settings → Actions → Runners → **New self-hosted runner** → Linux x64. The page shows the current download URL and a fresh registration `--token`.
2. On 10.80.2.251:

```bash
mkdir -p ~/actions-runner-viswall && cd ~/actions-runner-viswall
tar xzf ~/Downloads/actions-runner-linux-x64-<version>.tar.gz
./config.sh --url https://github.com/hrohrweck/viswall \
            --token <TOKEN_FROM_SETTINGS_PAGE> \
            --name viswall-runner-1 --labels viswall,self-hosted \
            --work _viswall-work
sudo ./svc.sh install && sudo ./svc.sh start
```

3. Verify the runner shows **Idle** under repo Settings → Actions → Runners. Until then, deploy jobs queue silently.

### 2. Prepare the server (viswall.webmasters.co.at)

The server must have a git checkout at `/opt/viswall` (the deploy pins it to the deployed commit because `shared/` is bind-mounted into api-gateway), a compose `.env`, and a user the workflow can SSH in as.

```bash
# --- on your machine: keypair for the workflow ---
ssh-keygen -t ed25519 -f viswall_deploy_key -N "" -C "github-actions-viswall-deploy"

# --- on the server ---
# dedicated deploy user with docker access
useradd -m -s /bin/bash -G docker viswall-deploy

# read-only deploy key so the server can `git fetch` (add viswall_deploy_key.pub
# as a deploy key with read access: repo Settings → Deploy keys)
sudo -u viswall-deploy git clone git@github.com:hrohrweck/viswall.git /opt/viswall
chown -R viswall-deploy:viswall-deploy /opt/viswall

# if an earlier deployment exists, reuse its .env (never committed):
#   /opt/viswall/deployments/docker/.env  ← DB_PASSWORD, JWT_SECRET_KEY, CORS_ORIGINS, …
# otherwise: cd /opt/viswall/deployments/docker && cp .env.example .env && editor .env

# install the workflow's public key
install -d -m 700 -o viswall-deploy -g viswall-deploy /home/viswall-deploy/.ssh
cat viswall_deploy_key.pub | sudo tee -a /home/viswall-deploy/.ssh/authorized_keys

# host key fingerprint (for SSH_FINGERPRINT — take the ED25519 line)
ssh-keyscan viswall.webmasters.co.at 2>/dev/null | ssh-keygen -lf -
```

Also add the workflow machine as an SSH client you accept: from the runner host,
`ssh viswall-deploy@viswall.webmasters.co.at` once to confirm reachability and
accept the host key.

### 3. Configure GitHub secrets and environment

```bash
gh secret set SSH_HOST        -R hrohrweck/viswall --body "viswall.webmasters.co.at"
gh secret set SSH_USER        -R hrohrweck/viswall --body "viswall-deploy"
gh secret set SSH_PRIVATE_KEY -R hrohrweck/viswall < viswall_deploy_key
gh secret set SSH_FINGERPRINT -R hrohrweck/viswall --body "SHA256:…(ED25519 line from above)"
gh api -X POST repos/hrohrweck/viswall/environments/production   # create the environment
```

GHCR images are private by default; the server logs in with the workflow's
`GITHUB_TOKEN` (`packages: write` covers pulling this repo's own packages).

### 4. First deploy

The `Deploy` workflow only auto-fires via `workflow_run` once it exists on
`main`. For the initial run: **Actions → Deploy → Run workflow
(workflow_dispatch)**, then verify:

```bash
ssh viswall-deploy@viswall.webmasters.co.at \
  'cd /opt/viswall/deployments/docker && docker compose -f docker-compose.yml -f docker-compose.prod.yml ps'
curl -sI https://viswall.webmasters.co.at/ | head -3
```

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
