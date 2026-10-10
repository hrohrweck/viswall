#!/usr/bin/env bash
# Remote deploy chain, executed on the prod host by viswall-deploy.
# Port of the retired deploy.yml SSH step's remote script, with
# vidforge-deploy's robustness (pre-pull retries + deploy.sh retries).
#
# Invocation (from the Jenkins agent):
#   { printf 'export GH_TOKEN=...'; cat this-file; } | ssh host 'bash -s' <image_tag> <full_sha>
#
# Args:   $1 = image tag (e.g. sha-1a2b3c4), $2 = full commit sha
# Stdin:  secret `export VAR=value` lines FIRST, then this script — secrets
#         travel over stdin, never as ssh argv. (They must precede the
#         script: bash -s read-ahead makes anything appended after the
#         body unreliable to read back via /dev/stdin.)

set -x

IMAGE_TAG="${1:?usage: deploy_remote.sh <image_tag> <full_sha>}"
GIT_SHA="${2:?usage: deploy_remote.sh <image_tag> <full_sha>}"

# /opt/viswall is the CD-managed checkout. Sync it BEFORE invoking
# deploy.sh: the script itself lives in the checkout.
cd /opt/viswall
git fetch origin main
git reset --hard "$GIT_SHA" 2>/dev/null || git reset --hard origin/main

echo "$GH_TOKEN" | docker login ghcr.io -u hrohrweck --password-stdin \
  || echo "WARNING: ghcr login failed - continuing with existing credentials"

# Pre-pull the new tag so a transient GHCR rejection (the registry
# occasionally answers 'denied: denied' to a login+manifest burst) can't
# turn the deploy into a rollback: deploy.sh's health gate cannot tell a
# rolled-back stack from a healthy one. Pull by explicit image reference.
PULL_OK=0
for pull_attempt in 1 2 3; do
  PULL_OK=1
  for img in api-gateway web-ui sogo dns-service; do
    docker pull "ghcr.io/hrohrweck/viswall/$img:$IMAGE_TAG" || PULL_OK=0
  done
  [ "$PULL_OK" = "1" ] && break
  echo "WARNING: image pull attempt $pull_attempt failed, retrying in 30s"
  sleep 30
done
if [ "$PULL_OK" != "1" ]; then
  echo "FATAL: docker pull failed after 3 attempts - aborting before deploy.sh (stack untouched)"
  exit 1
fi
docker image inspect "ghcr.io/hrohrweck/viswall/api-gateway:$IMAGE_TAG" >/dev/null 2>&1 \
  || { echo "FATAL: api-gateway image ghcr.io/hrohrweck/viswall/api-gateway:$IMAGE_TAG not present after pull - aborting"; exit 1; }

# deploy.sh is safely re-runnable (idempotent pin/backup/pull/up/gate with
# self-rollback). GHCR sometimes throttles the burst of manifest HEADs that
# follows our pre-pull, so retry before giving up. Short sleeps only: long
# idle periods have killed the ssh session mid-run (deploy #8 reported a
# false success), and the Jenkins job re-verifies .last-good-tag afterwards
# anyway.
#
# Exit code 3 means the post-deploy regression suite failed and deploy.sh
# already rolled the stack back to the previous tag. The outcome is
# deterministic — retrying would deploy the same bad version again — so
# give up immediately.
DEPLOY_OK=0
for deploy_attempt in 1 2 3; do
  set +e
  ./scripts/deploy.sh "$IMAGE_TAG" "$GIT_SHA"
  DEPLOY_RC=$?
  set -e
  if [ "$DEPLOY_RC" = "0" ]; then
    DEPLOY_OK=1
    break
  fi
  if [ "$DEPLOY_RC" = "3" ]; then
    echo "FATAL: post-deploy regression suite failed for $IMAGE_TAG — stack rolled back to the previous tag; not retrying"
    exit 3
  fi
  echo "WARNING: deploy.sh attempt $deploy_attempt exited with rc=$DEPLOY_RC (backups from each attempt are kept); retrying in 10s"
  sleep 10
done
if [ "$DEPLOY_OK" != "1" ]; then
  echo "FATAL: deploy.sh failed after 3 attempts - stack may have been rolled back"
  exit 1
fi

echo "LAST_GOOD_TAG=$(cat deployments/docker/.last-good-tag 2>/dev/null || echo missing)"
echo "Deployed $IMAGE_TAG ($GIT_SHA) successfully"
