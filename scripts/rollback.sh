#!/bin/bash
# Rollback: stop viswall mail-service and restore the legacy 'exim' container.
set -euo pipefail
BASE=/opt/viswall
COMPOSE_DIR="$BASE/viswall/deployments/docker"

echo "[rollback] stopping viswall mail-service"
cd "$COMPOSE_DIR"
docker compose --profile mail stop mail-service 2>/dev/null || true
docker compose --profile mail rm -f mail-service 2>/dev/null || true

echo "[rollback] starting legacy exim"
if docker start exim 2>/dev/null; then
  echo "[rollback] legacy exim started"
else
  echo "[rollback] container missing -> re-running start_exim.sh"
  bash "$BASE/start_exim.sh"
fi
sleep 5
for p in 25 587 993; do
  (exec 3<>/dev/tcp/127.0.0.1/"$p") 2>/dev/null && { echo "  $p open (legacy)"; exec 3>&-; } || echo "  $p CLOSED";
done
echo "[rollback] legacy restored"
