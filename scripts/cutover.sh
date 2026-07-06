#!/bin/bash
# Cutover: legacy 'exim' container -> viswall mail-service. RUN IN A MAINTENANCE WINDOW.
# The legacy container is stopped (NOT removed) so rollback.sh can restore it instantly.
set -euo pipefail
BASE=/opt/viswall
COMPOSE_DIR="$BASE/viswall/deployments/docker"
LEGACY_MAILDIR="$BASE/mail"
STAMP=$(date +%Y%m%d-%H%M%S)
BK="$BASE/_migration_backup/cutover-$STAMP"
mkdir -p "$BK"

echo "[cutover] 1/6 snapshot legacy maildir (25G) -> $BK/mail (borg repo is empty; do not rely on it)"
rsync -aH "$LEGACY_MAILDIR/" "$BK/mail/"

echo "[cutover] 2/6 ensure control-plane + data migration already done (postgres up, ETL committed)"
cd "$COMPOSE_DIR"
docker compose ps postgres >/dev/null

echo "[cutover] 3/6 stop legacy exim (kept for rollback)"
docker stop exim

echo "[cutover] 4/6 importing legacy maildirs into the mail_data volume"
# Ensure the login->domain/username map exists (regenerate if missing)
MAP="$BASE/_migration_backup/maildir_map.tsv"
[ -f "$MAP" ] || echo "WARN: $MAP missing — generate via migrate_legacy_mail.py --emit-map before cutover"
bash "$BASE/viswall/scripts/import_maildirs.sh" --run

echo "[cutover] 5/6 start viswall mail-service on real mail ports"
docker compose --profile mail up -d --build mail-service
sleep 8

echo "[cutover] 6/6 quick port check"
for p in 25 465 587 110 143 993 995; do
  (exec 3<>/dev/tcp/127.0.0.1/"$p") 2>/dev/null && { echo "  $p open"; exec 3>&-; } || echo "  $p CLOSED";
done
echo "[cutover] done. Run smoke tests (SMTP/IMAP/POP/TLS/SASL). If broken -> scripts/rollback.sh"
