#!/usr/bin/env bash
# Viswall server-side deploy: pin checkout, back up DB, pull prebuilt GHCR images,
# restart the stack, health-gate, and roll back to the last good tag on failure.
#
# Usage: ./scripts/deploy.sh <tag> <sha>
#   e.g. ./scripts/deploy.sh sha-abc1234 abc1234567890abcdef1234567890abcdef1234
#
# Invoked by .github/workflows/deploy.yml over SSH. Can also be run manually
# from the server checkout. See docs/DEPLOYMENT.md.
set -euo pipefail

TAG="${1:?usage: deploy.sh <tag> <sha>}"
SHA="${2:?usage: deploy.sh <tag> <sha>}"

DEPLOY_DIR="${DEPLOY_DIR:-/opt/viswall}"        # repo checkout on the server
COMPOSE_DIR="$DEPLOY_DIR/deployments/docker"
PUBLIC_HEALTH_URL="${PUBLIC_HEALTH_URL:-https://viswall.webmasters.co.at/}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-300}"         # seconds per health gate
BACKUP_DIR="${BACKUP_DIR:-$COMPOSE_DIR/backups}"
KEEP_BACKUPS=10
LAST_GOOD_FILE="$COMPOSE_DIR/.last-good-tag"

# Re-exec from a stable path: step 1 checks out a different commit, which would
# otherwise swap this script's file while bash is still reading it.
if [ "${VISWALL_DEPLOY_REEXEC:-}" != "1" ]; then
    _stable="${XDG_CACHE_HOME:-$HOME/.cache}/viswall/deploy.sh"
    mkdir -p "$(dirname "$_stable")"
    cp "$0" "$_stable"
    VISWALL_DEPLOY_REEXEC=1 exec "$_stable" "$@"
fi

log() { echo "[deploy] $*"; }

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

cd "$COMPOSE_DIR"

# ---------------------------------------------------------------------------
# 1. Pin the server checkout to the deployed commit.
#    shared/ is bind-mounted read-only into api-gateway and must match the
#    code baked into the image; compose files and this script also live here.
# ---------------------------------------------------------------------------
log "Syncing checkout to $SHA"
git -C "$DEPLOY_DIR" fetch origin main
if git -C "$DEPLOY_DIR" cat-file -e "$SHA^{commit}" 2>/dev/null; then
    git -C "$DEPLOY_DIR" reset --hard "$SHA"
else
    log "WARNING: $SHA not found locally — falling back to origin/main"
    git -C "$DEPLOY_DIR" reset --hard origin/main
fi

# ---------------------------------------------------------------------------
# 2. Database backup (before api-gateway startup runs alembic migrations).
# ---------------------------------------------------------------------------
mkdir -p "$BACKUP_DIR"
if docker compose -f docker-compose.yml ps --services --filter status=running | grep -qx postgres; then
    log "Dumping postgres backup"
    docker compose -f docker-compose.yml exec -T postgres \
        pg_dump -U viswall viswall \
        | gzip > "$BACKUP_DIR/viswall-$(date +%Y%m%d-%H%M%S).sql.gz" \
        || log "WARNING: pg_dump failed — continuing without a fresh backup"
    ls -1t "$BACKUP_DIR"/viswall-*.sql.gz 2>/dev/null | tail -n +"$((KEEP_BACKUPS + 1))" | xargs -r rm -f
else
    log "postgres not running — skipping backup"
fi

# ---------------------------------------------------------------------------
# 3. Pull the tagged images and apply.
# ---------------------------------------------------------------------------
log "Pulling images for tag $TAG"
VISWALL_TAG="$TAG" $COMPOSE pull
log "Applying stack at tag $TAG"
VISWALL_TAG="$TAG" $COMPOSE up -d --remove-orphans

# ---------------------------------------------------------------------------
# 4. Health gates.
# ---------------------------------------------------------------------------
api_healthy() {
    docker compose -f docker-compose.yml exec -T api-gateway python3 -c "
import sys, urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)
except Exception:
    sys.exit(1)
" 2>/dev/null
}

public_healthy() {
    curl -fsS --max-time 10 "$PUBLIC_HEALTH_URL" > /dev/null 2>&1
}

wait_for() {
    # wait_for <name> <check-cmd...>
    local name="$1"; shift
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if "$@"; then
            log "$name is healthy"
            return 0
        fi
        sleep 5
    done
    log "FAIL: $name did not become healthy within ${HEALTH_TIMEOUT}s"
    return 1
}

rollback() {
    if [ -f "$LAST_GOOD_FILE" ]; then
        OLD_TAG="$(cat "$LAST_GOOD_FILE")"
        log "Rolling back to $OLD_TAG"
        VISWALL_TAG="$OLD_TAG" $COMPOSE up -d --remove-orphans
    else
        # First deploy with no known-good tag: leave the stack as-is rather
        # than taking a live site down; an operator investigates from here.
        log "No .last-good-tag recorded — leaving current state in place"
    fi
    exit 1
}

wait_for "api-gateway /health" api_healthy || rollback
wait_for "public URL $PUBLIC_HEALTH_URL" public_healthy || rollback

# ---------------------------------------------------------------------------
# 5. Success: record the known-good tag, tidy up.
# ---------------------------------------------------------------------------
echo "$TAG" > "$LAST_GOOD_FILE"
docker image prune -f > /dev/null 2>&1 || true
log "Deployed $TAG ($SHA) successfully"
