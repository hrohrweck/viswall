#!/bin/bash
# Import legacy Courier maildirs (/data/mail/<login>) into the viswall mail_data volume
# at vhosts/<domain>/<username>/Maildir, using the login->domain/username map from the ETL
# (scripts/migrate_legacy_mail.py --emit-map). DRY-RUN by default; pass --run to copy.
set -euo pipefail
BASE=/opt/viswall
SRC="$BASE/mail"
MAP="${MAP:-$BASE/_migration_backup/maildir_map.tsv}"
VOL="${VOL:-viswall_mail_data}"
RUN=0; [ "${1:-}" = "--run" ] && RUN=1

[ -f "$MAP" ] || { echo "map not found: $MAP (generate via migrate_legacy_mail.py --emit-map)"; exit 1; }
echo "map=$MAP src=$SRC vol=$VOL run=$RUN"
total=0; missing=0
while IFS=$'\t' read -r login domain user; do
  [ -n "$login" ] || continue
  total=$((total+1))
  [ -d "$SRC/$login" ] || { echo "MISSING src maildir: $login"; missing=$((missing+1)); }
done < "$MAP"
echo "mappings=$total missing_src=$missing"
if [ "$RUN" != "1" ]; then
  echo "DRY-RUN only. Re-run with --run to copy into volume '$VOL'."
  exit 0
fi

# Copy via a helper container so we write into the named volume with correct ownership.
docker run --rm -v "$VOL":/dest -v "$SRC":/src:ro -v "$MAP":/map:ro alpine:latest sh -c '
  set -e
  tab=$(printf "\t")
  while IFS="$tab" read -r login domain user; do
    [ -n "$login" ] || continue
    s="/src/$login"; d="/dest/vhosts/$domain/$user/Maildir"
    if [ ! -d "$s" ]; then echo "skip missing: $login"; continue; fi
    mkdir -p "$d"
    cp -a "$s/." "$d/"
    echo "copied $login -> $domain/$user"
  done < /map
  chown -R 5000:5000 /dest/vhosts
'
echo "maildir import complete"
