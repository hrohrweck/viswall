# Viswall Jenkins CI/CD

Pipelines running on the self-hosted Jenkins at `http://10.80.2.251:8081`
(behind the `/jenkins-hook/` relay on the prod host nginx), mirroring the
vidForge setup. They replaced the retired `.github/workflows/ci.yml`,
`deploy.yml` and `sdk.yml` — GitHub remains only the source/PR host
(plus the lightweight `security.yml` gitleaks scan).

| Job | Script path | Purpose |
|---|---|---|
| `viswall-ci` | `ci/jenkins/Jenkinsfile` | PR + main tests: backend (Postgres/Redis sidecars), frontend, OpenAPI/SDK/CLI. PRs get a `jenkins-ci` commit status; a green main build triggers `viswall-release`. |
| `viswall-release` | `ci/jenkins/Jenkinsfile.release` | buildx-build `api-gateway`, `web-ui`, `sogo`, `dns-service` and push to `ghcr.io/hrohrweck/viswall/*` tagged `sha-<short7>` + `main` (registry `:buildcache`). Triggers `viswall-deploy`. |
| `viswall-deploy` | `ci/jenkins/Jenkinsfile.deploy` | SSH to `viswall-deploy@viswall.webmasters.co.at`, pre-pull the images (retries), run `scripts/deploy.sh <tag> <sha>` (checkout pin, pg_dump backup, apply, health gates, auto-rollback). |
| `viswall-approve` | `ci/jenkins/Jenkinsfile.approve` | `/approve` comment by the PR author self-approves the PR via the vidforge-bot PAT (the "Protect main" ruleset requires 1 approval). |

Webhook: one repo webhook for `push`, `pull_request`, `issue_comment` →
`https://viswall.webmasters.co.at/jenkins-hook/generic-webhook-trigger/invoke?token=<viswall-gwt-token>`.
Jobs are isolated from the vidforge jobs by the dedicated `viswall-gwt-token`
credential (GWT only invokes jobs whose token matches).

Manual runs: trigger `viswall-release` with `GIT_SHA` (empty = main HEAD);
set `SKIP_DEPLOY=true` to build without deploying. `viswall-deploy` can be
run manually with `GIT_SHA` + `IMAGE_TAG` to redeploy an existing tag.

Jenkins credentials used: `viswall-gwt-token` (webhook token),
`viswall-deploy-ssh` (deploy key for the prod server),
`viswall-github-pat` (hrohrweck classic PAT, `repo` + `write:packages` —
commit statuses, GHCR push/pull for this repo's packages).
`viswall-approve` uses the vidforge-bot PAT for PR reviews (approving
hrohrweck-authored PRs with the owner token would be self-approval and
is rejected by GitHub).
