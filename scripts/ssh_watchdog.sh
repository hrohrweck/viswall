#!/usr/bin/env bash
# ssh_watchdog.sh — host-native dead-man-switch PROBER for the viswall firewall
# migration (plan todo 40). Proof-gated sliding-window revert trap.
#
# Installed at cutover (todo 44) as /usr/local/sbin/ssh_watchdog.sh and started
# by deployments/docker/viswall-ssh-watchdog.service (copied to
# /etc/systemd/system — this script never installs anything itself).
#
# Semantics (todo 40, round-3 corrected design):
#   - Loop every INTERVAL seconds (default 30).
#   - If $STATE_DIR/COMMIT exists (cutover committed) the trap is frozen:
#     log and skip the cycle — touch NOTHING.
#   - Otherwise evaluate ALL proof-of-life checks. ONLY if every check passes
#     does the prober:
#       1. touch $STATE_DIR/ALIVE            (fresh proof for restore_firewall.sh's
#                                             120 s no-op guard, todo 10)
#       2. systemctl stop vw-revert.timer vw-revert.service  (errors tolerated)
#       3. systemd-run --on-active=15m --unit=vw-revert \
#            /usr/local/sbin/restore_firewall.sh $RESTORE_FLAGS
#       4. verify `systemctl is-active vw-revert.timer`; if not active, log
#          "RE-ARM FAILED" and retry next cycle (a silently missing trap is
#          unacceptable — Oracle round-5 #3).
#   - On ANY failed check: touch NOTHING. The armed timer keeps its countdown
#     and fires the restore on expiry — the deadline slides ONLY with
#     proof-of-life, so the trap fires when SSH dies, not merely when the
#     prober dies (Oracle round-4 #1). Fail closed everywhere.
#
# Proof-of-life checks:
#   (a) FRESH SSH login (loopback): the probe runs a real `ssh` with
#       BatchMode + ConnectTimeout=5, so a dead sshd or a firewall that kills
#       tcp/22 makes the probe time out and FAIL the proof:
#         ssh -i $SSH_KEY -p $SSH_PORT -o BatchMode=yes \
#             -o ConnectTimeout=5 -o StrictHostKeyChecking=no $SSH_TARGET true
#       SSH_KEY is an unencrypted identity file supplied by the operator at
#       deploy time. Unset SSH_KEY or missing ssh binary = FAIL (fail closed).
#   (b) gateway health: curl -fsS -m 5 $GATEWAY_HEALTH_URL
#       (default http://127.0.0.1:8010/health). Non-2xx/timeout = FAIL.
#   (c) WireGuard: `wg show client latest-handshakes` — the latest-handshake
#       age must be < $WG_MAX_AGE (default 300 s). Skipped (neutral, with a
#       warning) under --ignore-wg (todo 42 deliberate stop drill) or when the
#       wg binary is absent.
#   (d) drift: the normalized hash of `nft -j list table inet viswall` is
#       compared against $REFERENCE_FILE (default
#       $STATE_DIR/ref-normalized.hash), written by the firewall agent after
#       every successful /firewall/apply (todo 7b/8). If the reference file is
#       ABSENT the trap is not yet armed → drift is OK. Any mismatch (or an
#       un-sampleable ruleset) = FAIL. This is the WAN-path guard: a
#       policy-routing/interface mutation that kills only WAN tcp/22 shows up
#       here (todo 40 Oracle round-5 #2 / round-3 blocker #2).
#
#   NORMALIZED-HASH CONTRACT (the firewall agent's reference writer MUST
#   produce this exact form, or every cycle reads as drift):
#     json.load the `nft -j list table inet viswall` output, recursively delete
#     the keys: elem, counter, bytes, packets, expires, handle; then
#     json.dumps(sort_keys=True, separators=(",", ":")); then sha256. The
#     reference file's first whitespace-delimited token is the hex digest
#     (a plain `sha256sum`-style line is also accepted for the same reason).
#
# Flags:
#   --dry-run    print every MUTATING action (touch ALIVE, systemctl stop,
#                systemd-run) instead of executing it. Probes and the
#                is-active verification still run (the todo-41 drill points
#                the binaries at recorder scripts). Real read-only probes on
#                a real host are harmless in dry-run.
#   --ignore-wg  bypass the WireGuard handshake check (todo 42 stop drill).
#
# Env overrides (all optional; defaults tuned for todos 40-43):
#   INTERVAL, MAX_CYCLES (0 = run forever; non-zero aids drills),
#   STATE_DIR, REFERENCE_FILE, SSH_TARGET, SSH_PORT, SSH_KEY,
#   GATEWAY_HEALTH_URL, WG_MAX_AGE,
#   RESTORE_FLAGS (default "--no-restart-docker"; todo 44 sets it EMPTY for
#   the full restore — note the distinction between unset and empty),
#   RESTORE_SCRIPT (default /usr/local/sbin/restore_firewall.sh),
#   and the binaries: SSH, CURL, WG, NFT, SYSTEMCTL, SYSTEMD_RUN, STAT,
#   TOUCH, PYTHON3, SHA256SUM.
#
# Everything is logged to stderr (journald) with an [ssh-watchdog] prefix.
# The script never exits on a failed probe; it keeps probing.

set -uo pipefail

# --- config (env-overridable) ---------------------------------------------
INTERVAL="${INTERVAL:-30}"
MAX_CYCLES="${MAX_CYCLES:-0}"
STATE_DIR="${STATE_DIR:-/var/lib/viswall-firewall}"
REFERENCE_FILE="${REFERENCE_FILE:-$STATE_DIR/ref-normalized.hash}"
SSH_TARGET="${SSH_TARGET:-127.0.0.1}"
SSH_PORT="${SSH_PORT:-22}"
GATEWAY_HEALTH_URL="${GATEWAY_HEALTH_URL:-http://127.0.0.1:8010/health}"
WG_MAX_AGE="${WG_MAX_AGE:-300}"
# Unset -> rehearsal default; EMPTY -> full restore (todo 44 sets it empty).
RESTORE_FLAGS="${RESTORE_FLAGS---no-restart-docker}"
RESTORE_SCRIPT="${RESTORE_SCRIPT:-/usr/local/sbin/restore_firewall.sh}"

SSH="${SSH:-ssh}"
CURL="${CURL:-curl}"
WG="${WG:-wg}"
NFT="${NFT:-nft}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
SYSTEMD_RUN="${SYSTEMD_RUN:-systemd-run}"
STAT="${STAT:-stat}"
TOUCH="${TOUCH:-touch}"
PYTHON3="${PYTHON3:-python3}"
SHA256SUM="${SHA256SUM:-sha256sum}"

COMMIT_MARKER="$STATE_DIR/COMMIT"
ALIVE_FILE="$STATE_DIR/ALIVE"
REVERT_TIMER="vw-revert.timer"
REVERT_SERVICE="vw-revert.service"
REVERT_UNIT="vw-revert"
REVERT_WINDOW="15m"

DRY_RUN=0
IGNORE_WG=0

# --- helpers ---------------------------------------------------------------
log() {
    printf '[ssh-watchdog %s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >&2
}

binary_present() {
    [ -n "${1:-}" ] && command -v "$1" >/dev/null 2>&1
}

usage() {
    cat >&2 <<EOF
usage: $0 [--dry-run] [--ignore-wg]

  --dry-run    print mutating actions (touch ALIVE / systemctl stop /
               systemd-run) instead of executing them; probes and the
               is-active verification still run.
  --ignore-wg  bypass the WireGuard handshake check.

Env: INTERVAL MAX_CYCLES STATE_DIR REFERENCE_FILE SSH_TARGET SSH_PORT
SSH_KEY GATEWAY_HEALTH_URL WG_MAX_AGE RESTORE_FLAGS RESTORE_SCRIPT
SSH CURL WG NFT SYSTEMCTL SYSTEMD_RUN STAT TOUCH PYTHON3 SHA256SUM
EOF
    exit 2
}

# --- proof checks (each logs PASS/FAIL/SKIP and returns 0 only when passed) --
check_ssh() {
    if ! binary_present "$SSH"; then
        log "check ssh: FAIL (ssh binary '$SSH' not found — fail closed)"
        return 1
    fi
    if [ -z "${SSH_KEY:-}" ]; then
        log "check ssh: FAIL (SSH_KEY unset — deploy-time identity required)"
        return 1
    fi
    if "$SSH" -i "$SSH_KEY" -p "$SSH_PORT" -o BatchMode=yes \
        -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$SSH_TARGET" true >/dev/null 2>&1; then
        log "check ssh: OK (fresh login to $SSH_TARGET:$SSH_PORT)"
        return 0
    fi
    log "check ssh: FAIL (login to $SSH_TARGET:$SSH_PORT failed or timed out)"
    return 1
}

check_health() {
    if ! binary_present "$CURL"; then
        log "check health: FAIL (curl binary '$CURL' not found — fail closed)"
        return 1
    fi
    if "$CURL" -fsS -m 5 "$GATEWAY_HEALTH_URL" >/dev/null 2>&1; then
        log "check health: OK ($GATEWAY_HEALTH_URL)"
        return 0
    fi
    log "check health: FAIL ($GATEWAY_HEALTH_URL unreachable or non-2xx)"
    return 1
}

wg_age_seconds() {
    # "latest handshake: 1 minute, 30 seconds ago" -> 90; "42 seconds ago" -> 42
    printf '%s\n' "$1" | sed -E 's/^.*latest handshake: //' | awk '{
        total = 0
        for (i = 1; i <= NF; i += 1) {
            n = $i; unit = $(i + 1); gsub(/,/, "", unit)
            if (unit == "second" || unit == "seconds") total += n
            else if (unit == "minute" || unit == "minutes") total += n * 60
            else if (unit == "hour" || unit == "hours") total += n * 3600
            else if (unit == "day" || unit == "days") total += n * 86400
        }
        printf "%d", total
    }'
}

check_wg() {
    if [ "$IGNORE_WG" -eq 1 ]; then
        log "check wg: SKIPPED (--ignore-wg)"
        return 0
    fi
    if ! binary_present "$WG"; then
        log "check wg: SKIPPED (wg binary '$WG' not found — bypassed with warning)"
        return 0
    fi
    local out line age
    out=$("$WG" show client latest-handshakes 2>/dev/null) || {
        log "check wg: FAIL (wg show client failed — interface down or missing)"
        return 1
    }
    line=$(printf '%s\n' "$out" | grep -m1 'latest handshake') || {
        log "check wg: FAIL (no handshake recorded)"
        return 1
    }
    age=$(wg_age_seconds "$line")
    case "$age" in
        ''|*[!0-9]*)
            log "check wg: FAIL (unparseable handshake line: $line)"
            return 1
            ;;
    esac
    if [ "$age" -lt "$WG_MAX_AGE" ]; then
        log "check wg: OK (handshake age ${age}s < ${WG_MAX_AGE}s)"
        return 0
    fi
    log "check wg: FAIL (handshake age ${age}s >= ${WG_MAX_AGE}s)"
    return 1
}

NORMALIZE_JSON='import json, sys
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items()
                if k not in ("elem", "counter", "bytes", "packets", "expires", "handle")}
    if isinstance(o, list):
        return [strip(x) for x in o]
    return o
d = json.load(sys.stdin)
print(json.dumps(strip(d), sort_keys=True, separators=(",", ":")))'

check_drift() {
    if [ ! -s "$REFERENCE_FILE" ]; then
        log "check drift: OK (reference absent: $REFERENCE_FILE — not yet armed)"
        return 0
    fi
    local bin ref live
    for bin in "$NFT" "$PYTHON3" "$SHA256SUM"; do
        if ! binary_present "$bin"; then
            log "check drift: FAIL (required binary '$bin' not found — fail closed)"
            return 1
        fi
    done
    ref=$(awk '{ print $1; exit }' "$REFERENCE_FILE")
    live=$("$NFT" -j list table inet viswall 2>/dev/null \
        | "$PYTHON3" -c "$NORMALIZE_JSON" \
        | "$SHA256SUM" | awk '{ print $1 }') || live=""
    case "$live" in
        ''|*[!0-9a-fA-F]*)
            log "check drift: FAIL (could not sample or normalize nft ruleset)"
            return 1
            ;;
    esac
    if [ "$live" = "$ref" ]; then
        log "check drift: OK (normalized hash matches reference)"
        return 0
    fi
    log "check drift: FAIL (normalized hash mismatch: live=$live ref=$ref)"
    return 1
}

# --- trap re-arm (precondition: every proof check passed) -------------------
rearm_trap() {
    if ! binary_present "$TOUCH" \
        || ! binary_present "$SYSTEMCTL" \
        || ! binary_present "$SYSTEMD_RUN"; then
        log "RE-ARM FAILED: missing binary (touch/systemctl/systemd-run) — retry next cycle"
        return 1
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $TOUCH $ALIVE_FILE"
    else
        if ! "$TOUCH" "$ALIVE_FILE"; then
            log "ALIVE TOUCH FAILED — aborting re-arm this cycle (no fresh proof-of-life recorded)"
            return 1
        fi
        log "ALIVE touched: $($STAT -c '%y' "$ALIVE_FILE" 2>/dev/null || true)"
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        log "[DRY-RUN] would run: $SYSTEMCTL stop $REVERT_TIMER $REVERT_SERVICE (errors tolerated)"
    else
        "$SYSTEMCTL" stop "$REVERT_TIMER" "$REVERT_SERVICE" 2>/dev/null || true
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        # shellcheck disable=SC2086  # RESTORE_FLAGS is an intentional word-split list
        log "[DRY-RUN] would run: $SYSTEMD_RUN --on-active=$REVERT_WINDOW --unit=$REVERT_UNIT $RESTORE_SCRIPT $RESTORE_FLAGS"
    elif ! "$SYSTEMD_RUN" --on-active="$REVERT_WINDOW" --unit="$REVERT_UNIT" \
        "$RESTORE_SCRIPT" $RESTORE_FLAGS; then
        log "RE-ARM FAILED: systemd-run exited non-zero — retry next cycle"
        return 1
    fi

    local is_active
    # `is-active` exits non-zero for "inactive": that rc is the signal and its
    # stdout (inactive/failed) is the diagnostic — neither may be swallowed.
    is_active=$("$SYSTEMCTL" is-active "$REVERT_TIMER" 2>/dev/null)
    if [ "$is_active" != "active" ]; then
        log "RE-ARM FAILED: $REVERT_TIMER is-active='${is_active:-<no output>}' (expected active) — retry next cycle"
        return 1
    fi
    log "RE-ARM OK: $REVERT_TIMER active, window $REVERT_WINDOW"
    return 0
}

# --- one cycle --------------------------------------------------------------
run_cycle() {
    if [ -e "$COMMIT_MARKER" ]; then
        log "COMMIT present ($COMMIT_MARKER) — cutover committed; trap frozen, touching nothing this cycle"
        return 0
    fi

    local ssh_ok=1 health_ok=1 wg_ok=1 drift_ok=1
    check_ssh;    ssh_ok=$?
    check_health; health_ok=$?
    check_wg;     wg_ok=$?
    check_drift;  drift_ok=$?

    if [ "$ssh_ok" -ne 0 ] || [ "$health_ok" -ne 0 ] \
        || [ "$wg_ok" -ne 0 ] || [ "$drift_ok" -ne 0 ]; then
        log "proof FAILED (ssh=$ssh_ok health=$health_ok wg=$wg_ok drift=$drift_ok) — touching NOTHING; armed timer keeps its countdown"
        return 0
    fi

    log "proof OK — re-arming the revert trap"
    rearm_trap
}

# --- main -------------------------------------------------------------------
main() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --dry-run) DRY_RUN=1 ;;
            --ignore-wg) IGNORE_WG=1 ;;
            -h|--help) usage ;;
            *)
                log "error: unknown option: $1"
                usage
                ;;
        esac
        shift
    done

    log "ssh-watchdog start (interval=${INTERVAL}s max_cycles=$MAX_CYCLES dry_run=$DRY_RUN ignore_wg=$IGNORE_WG state=$STATE_DIR)"
    local cycles=0
    while :; do
        run_cycle
        cycles=$((cycles + 1))
        if [ "$MAX_CYCLES" -gt 0 ] && [ "$cycles" -ge "$MAX_CYCLES" ]; then
            log "ssh-watchdog stop (MAX_CYCLES=$MAX_CYCLES reached)"
            return 0
        fi
        sleep "$INTERVAL"
    done
}

main "$@"
