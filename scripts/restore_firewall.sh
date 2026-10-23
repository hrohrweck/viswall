#!/usr/bin/env bash
# restore_firewall.sh — host-native emergency restore of the pre-migration firewall.
#
# Usage: restore_firewall.sh [--dry-run] [--no-restart-docker] <snapshot-dir>
#
# The dead-man-switch revert path (deployed to /usr/local/sbin/restore_firewall.sh
# in todo 44). Host-native on purpose: it must work even when the viswall
# containers are what broke, so it never depends on the agent or console.
#
# Sequence (order is deliberate):
#   1. No-op guard FIRST, before anything else: exit 0 if $STATE_DIR/COMMIT
#      exists (cutover committed) or $STATE_DIR/ALIVE has mtime < 120 s
#      (current proof-of-life — a fired trap with fresh proof-of-life is a
#      scheduled no-op, never a restore). A scheduled no-op must never
#      mutate anything, so this guard runs BEFORE the destructive steps.
#   2. Remove the viswall layer: disable viswall-firewall-persist and
#      `nft delete table inet viswall` (never a flush). The viswall input hook
#      runs at priority -200, before iptables filter, so iptables-restore alone
#      cannot revert the very failure this script exists for.
#   3. Validate the snapshot with iptables-restore --test / ip6tables-restore
#      --test BEFORE touching the live rules (a corrupt snapshot must never
#      leave iptables half-loaded).
#   4. Copy rules.v4/rules.v6 back to /etc/iptables/ and re-enable
#      netfilter-persistent (boot-time protection is back immediately).
#   5. iptables-restore -w 30 && ip6tables-restore -w 30 (-w avoids racing
#      docker's iptables lock).
#   6. systemctl restart docker (rebuilds docker chains) unless
#      --no-restart-docker (rehearsals only).
#   7. systemctl restart wg-quick@client.
#   8. Copy the snapshot's netplan/ back to /etc/netplan and `netplan apply`.
#
# Everything is logged to /var/log/viswall-restore.log. Safe to run repeatedly.
set -euo pipefail

LOG="${LOG:-/var/log/viswall-restore.log}"
STATE_DIR="${STATE_DIR:-/var/lib/viswall-firewall}"
COMMIT_MARKER="$STATE_DIR/COMMIT"
ALIVE_FILE="$STATE_DIR/ALIVE"
ALIVE_MAX_AGE_SEC=120

DRY_RUN=0
RESTART_DOCKER=1

usage() {
    cat >&2 <<EOF
usage: $0 [--dry-run] [--no-restart-docker] <snapshot-dir>

  --dry-run            print every command instead of executing it
  --no-restart-docker  skip the docker restart (rehearsals only)
EOF
    exit 2
}

log() {
    local msg
    msg="$(date '+%Y-%m-%dT%H:%M:%S%z') $*"
    printf '%s\n' "$msg" | tee -a "$LOG" 2>/dev/null || true
}

run() {
    # execute (or print) a command, failing the script on non-zero exit
    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $*"
        return 0
    fi
    log "running: $*"
    "$@"
}

run_tolerant() {
    # expected-to-fail command (missing unit / missing nft table): never fatal
    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $* (errors tolerated)"
        return 0
    fi
    log "running: $* (errors tolerated)"
    "$@" 2>/dev/null || true
}

_test_before_restore() {
    local bin="$1" file="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $bin --test < $file"
        return 0
    fi
    log "running: $bin --test < $file"
    if ! "$bin" --test < "$file"; then
        log "FATAL: $bin --test failed on $file — aborting before touching the live rules"
        exit 1
    fi
}

_restore_family() {
    local bin="$1" file="$2"
    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $bin -w 30 < $file"
        return 0
    fi
    log "running: $bin -w 30 < $file"
    if ! "$bin" -w 30 < "$file"; then
        log "FATAL: $bin -w 30 < $file failed"
        exit 1
    fi
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        --no-restart-docker) RESTART_DOCKER=0; shift ;;
        -h|--help) usage ;;
        -*) echo "error: unknown option: $1" >&2; usage ;;
        *) break ;;
    esac
done

SNAPSHOT_DIR="${1:-}"
if [ -z "$SNAPSHOT_DIR" ]; then
    echo "error: missing <snapshot-dir> argument" >&2
    usage
fi
if [ ! -d "$SNAPSHOT_DIR" ]; then
    log "FATAL: snapshot dir not found: $SNAPSHOT_DIR"
    exit 2
fi

log "=== restore_firewall.sh start (snapshot: $SNAPSHOT_DIR)"

# 1. No-op guard FIRST: committed cutover or fresh proof-of-life -> nothing to
#    do. Runs before any destructive command — a scheduled no-op never mutates.
if [ -e "$COMMIT_MARKER" ]; then
    log "no-op: $COMMIT_MARKER exists (cutover committed) — exiting 0 without restoring"
    exit 0
fi
if [ -f "$ALIVE_FILE" ]; then
    alive_age=$(( $(date +%s) - $(stat -c %Y "$ALIVE_FILE") ))
    if [ "$alive_age" -lt "$ALIVE_MAX_AGE_SEC" ]; then
        log "no-op: $ALIVE_FILE mtime ${alive_age}s < ${ALIVE_MAX_AGE_SEC}s (proof-of-life fresh) — exiting 0 without restoring"
        exit 0
    fi
    log "guard: $ALIVE_FILE age ${alive_age}s >= ${ALIVE_MAX_AGE_SEC}s — proceeding with restore"
fi

# 2. Remove the viswall layer (see header comment).
run_tolerant systemctl disable --now viswall-firewall-persist
run_tolerant nft delete table inet viswall

# 3. Validate before touching anything (corrupt snapshot must not half-load).
if [ ! -f "$SNAPSHOT_DIR/rules.v4" ] || [ ! -f "$SNAPSHOT_DIR/rules.v6" ]; then
    log "FATAL: snapshot is missing rules.v4 and/or rules.v6: $SNAPSHOT_DIR"
    exit 2
fi
_test_before_restore iptables-restore "$SNAPSHOT_DIR/rules.v4"
_test_before_restore ip6tables-restore "$SNAPSHOT_DIR/rules.v6"

# 4. Put the files back for boot and re-enable the boot loader.
run cp "$SNAPSHOT_DIR/rules.v4" /etc/iptables/rules.v4
run cp "$SNAPSHOT_DIR/rules.v6" /etc/iptables/rules.v6
run chmod 0640 /etc/iptables/rules.v4 /etc/iptables/rules.v6
run systemctl enable netfilter-persistent

# 5. Restore both families (v4 first; a v4 failure aborts before v6).
_restore_family iptables-restore "$SNAPSHOT_DIR/rules.v4"
_restore_family ip6tables-restore "$SNAPSHOT_DIR/rules.v6"

# 6. Docker rebuilds its chains.
if [ "$RESTART_DOCKER" -eq 1 ]; then
    run systemctl restart docker
else
    log "skipping docker restart (--no-restart-docker)"
fi

# 7. Bring the site-to-site tunnel back.
run systemctl restart wg-quick@client

# 8. Netplan copy-back + apply.
if [ -d "$SNAPSHOT_DIR/netplan" ]; then
    run cp -a "$SNAPSHOT_DIR/netplan/." /etc/netplan/
    run netplan apply
else
    log "skipping netplan restore (no netplan/ in snapshot)"
fi

log "=== restore_firewall.sh complete"
