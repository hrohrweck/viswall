# Migration Guide: Legacy Exim → Viswall Mail Platform

## Overview

This guide covers migrating a legacy single-container mail server (Exim + Courier IMAP/POP3 + MariaDB + SpamAssassin, launched by `start_exim.sh` with `--network host`) to the Viswall mail platform: a multi-container Docker Compose stack with Postgres, Dovecot, Exim, and SOGo.

The migration was performed on this host on **2026-07-04** with approximately **32 seconds** of downtime, using pre-staging (image built and 25 GB of maildirs copied while the legacy container still served mail).

## Prerequisites

- Docker + Docker Compose on the target host.
- The Viswall repository checked out at `/opt/viswall/viswall`.
- Sufficient disk space: legacy maildir size + 2x for backup + new volume.
- A maintenance window. Expect ~5 minutes with pre-staging, ~30 minutes without.
- DNS access for MX/SPF/DKIM record updates.

## Phase 1: Assess the Legacy System

Inventory the legacy container and its database before touching anything.

List domains in the legacy MariaDB `exim` database:

```sql
SELECT * FROM LocalMailDomains;
SELECT * FROM AdditionalMailDomains;
```

List mailboxes. Note that `Passwort` is stored in cleartext:

```sql
SELECT login, Passwort, quota FROM Mailusers;
```

List aliases:

```sql
SELECT Email, Forwarder FROM Aliases;
```

Measure the maildir footprint and database on the host:

```bash
du -sh /opt/viswall/mail/
du -sh /opt/viswall/mysql/
```

Also document:

- TLS certificate paths (Let's Encrypt live directory).
- HELO hostname (`mail.example.com` in this deployment).
- Port bindings: 25, 465, 587, 110, 143, 993, 995.
- Any custom Exim routers or transports under `/etc/exim4`.
- Courier auth settings under `/etc/courier` (especially `authmysqlrc`).

## Phase 2: Cold Backup

Stop or quiesce the legacy container, then snapshot everything needed for rollback.

```bash
# Stop legacy mail flow
docker stop exim

# Snapshot directory (adjust STAMP as needed)
STAMP=$(date +%Y%m%d-%H%M%S)
BK="/opt/viswall/_migration_backup/$STAMP"
mkdir -p "$BK"

# Save the legacy image
docker save exim:latest > "$BK/exim-image.tar"

# Dump the legacy databases
mysqldump -h 127.0.0.1 -u viswall -p exim > "$BK/db-exim.sql"
mysqldump -h 127.0.0.1 -u viswall -p spamassassin > "$BK/db-spamassassin.sql"
mysqldump -h 127.0.0.1 -u viswall -p viswall > "$BK/db-viswall.sql"

# Save TLS certs, configs, launcher, and inspect output
cp /opt/nginx/config/letsencrypt/live/mail.example.com/fullchain.pem "$BK/certs/"
cp /opt/nginx/config/letsencrypt/live/mail.example.com/privkey.pem "$BK/certs/"
cp /opt/viswall/start_exim.sh "$BK/"
docker inspect exim > "$BK/exim.inspect.json"

# Copy Exim and Courier configs from the legacy container
mkdir -p "$BK/legacy-etc-exim4" "$BK/legacy-etc-courier"
docker cp exim:/etc/exim4/. "$BK/legacy-etc-exim4/"
docker cp exim:/etc/courier/. "$BK/legacy-etc-courier/"

# Optional: snapshot maildirs (heavy). The import script is read-only on source,
# but a snapshot is useful for insurance.
rsync -aH /opt/viswall/mail/ "$BK/mail/"
```

The actual backup set used for this migration is at `_migration_backup/<TIMESTAMP>/` and contains:

| File | Size | Purpose |
|---|---|---|
| `exim-image.tar` | ~1.4 GB | Legacy container image |
| `db-exim.sql` | ~4.1 GB | Legacy MariaDB `exim` dump |
| `db-exim.schema.sql` | 17 KB | Schema-only dump |
| `db-spamassassin.sql` | ~1 KB | SpamAssassin DB |
| `db-viswall.sql` | ~1 KB | Viswall MariaDB data (legacy) |
| `certs/` | 4 KB | TLS fullchain + privkey |
| `legacy-etc-exim4/` | 4 KB | `/etc/exim4` from the legacy container |
| `legacy-etc-courier/` | 4 KB | `/etc/courier` from the legacy container |
| `start_exim.sh` | 1.4 KB | Legacy launcher |
| `exim.inspect.json` | 15 KB | `docker inspect exim` output |
| `mail_agent.py.orig` | 30 KB | Original mail agent script |
| `borg.listing.txt` | 95 B | Empty borg repo listing at backup time |

Verify the backup is complete before proceeding. In particular, confirm `exim-image.tar` can be loaded:

```bash
docker load < "$BK/exim-image.tar"
```

## Phase 3: Database Migration (ETL)

The ETL script is `viswall/scripts/migrate_legacy_mail.py`. It reads the legacy MariaDB `exim` database and writes domains, mailboxes, and aliases into Postgres. Cleartext passwords are re-hashed to bcrypt.

Requirements:

- Python 3 with `pymysql`, `psycopg2-binary`, and `bcrypt` installed.
- A reachable legacy MariaDB instance (for this migration, a throwaway MariaDB container loaded from the `db-exim.sql` dump was used).
- A reachable Postgres `viswall` database.

Environment variables the script expects (defaults are shown):

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=viswall
export MYSQL_PASSWORD=""          # legacy MariaDB password
export MYSQL_DB=exim
export PG_HOST=127.0.0.1
export PG_PORT=5432
export PG_USER=viswall
export PG_PASSWORD=""             # Postgres password
export PG_DB=viswall
```

Dry run first (no `--commit`):

```bash
cd /opt/viswall/viswall
python scripts/migrate_legacy_mail.py --default-domain example.com
```

Review the output carefully:

- Domain count (expected 29).
- Mailbox count and any `UNRESOLVED bare` logins.
- Alias count and catch-all count.
- Identity overrides if used.

For logins that do not map cleanly to `username@domain`, create an overrides TSV:

```bash
# _migration_backup/identity_overrides.tsv
# login<TAB>username<TAB>domain
user1	user1	example.com
user2	user2	example.com
akia2ws3ce3hbq2ypwr4	DROP
```

Then run with overrides:

```bash
python scripts/migrate_legacy_mail.py \
  --default-domain example.com \
  --overrides _migration_backup/identity_overrides.tsv
```

When the preview looks correct, commit:

```bash
python scripts/migrate_legacy_mail.py \
  --default-domain example.com \
  --overrides _migration_backup/identity_overrides.tsv \
  --commit
```

Emit the maildir map for Phase 4:

```bash
python scripts/migrate_legacy_mail.py \
  --default-domain example.com \
  --overrides _migration_backup/identity_overrides.tsv \
  --emit-map _migration_backup/maildir_map.tsv
```

The map has one row per mailbox: `login<TAB>domain<TAB>username`.

## Phase 4: Maildir Import

Use `viswall/scripts/import_maildirs.sh` to copy legacy Courier maildirs into the Viswall `mail_data` volume. The script is dry-run by default; pass `--run` to copy.

Review the plan:

```bash
bash /opt/viswall/viswall/scripts/import_maildirs.sh
```

Expected output shows the number of mappings and any missing source directories. When ready, run the import:

```bash
bash /opt/viswall/viswall/scripts/import_maildirs.sh --run
```

What the script does:

- Reads `_migration_backup/maildir_map.tsv`.
- Copies `/opt/viswall/mail/<login>/` to `vhosts/<domain>/<username>/Maildir` inside the `viswall_mail_data` volume.
- Runs `chown -R 5000:5000 /dest/vhosts` so Dovecot's `vmail` user owns the mail.

The legacy maildirs already contain `dovecot-uidlist` and `dovecot-uidvalidity`, so Dovecot UIDs are preserved.

## Phase 5: DNS Preparation

Before cutover, make sure DNS is ready:

- **MX record:** ensure it points to the new server's IP. If the migration stays on the same host, the IP does not change.
- **SPF:** update only if the sending IP changed (usually unchanged on the same host).
- **DKIM:** generate a key, publish the TXT record with a selector and public key. This deployment uses selector `viswall` for `example.com` only.
- **DMARC:** publish or update if desired.
- **TTL:** consider lowering TTLs before the cutover window so rollback propagates faster.

The DKIM public key for this deployment is:

```
viswall._domainkey.example.com.  IN  TXT  "v=DKIM1; k=rsa; p=<your-base64-public-key>"
```

## Phase 6: Cutover

The orchestrated cutover script is `viswall/scripts/cutover.sh`. For minimum downtime, pre-stage the work while the legacy container still runs:

1. Pre-build the `mail-service` image:

   ```bash
   cd /opt/viswall/viswall/deployments/docker
   docker compose --profile mail build mail-service
   ```

2. Pre-seed the `mail_data` volume with the maildir import (read-only on source).

3. In the maintenance window, run the cutover script:

   ```bash
   bash /opt/viswall/viswall/scripts/cutover.sh
   ```

The script performs these steps:

1. Snapshots the legacy maildir to `_migration_backup/cutover-<STAMP>/mail/`.
2. Verifies Postgres is running.
3. Stops the legacy `exim` container (kept, not removed).
4. Runs `import_maildirs.sh --run`.
5. Starts `mail-service` under the `mail` profile.
6. Checks that ports 25, 465, 587, 110, 143, 993, 995 respond on localhost.

For this deployment, the actual cutover was run as an optimized manual sequence: stop legacy Exim, rsync the delta of 34 mailboxes, then start `mail-service`. Downtime was approximately **32 seconds**.

### Manual cutover steps

If you prefer not to use `cutover.sh`:

```bash
BASE=/opt/viswall
COMPOSE_DIR="$BASE/viswall/deployments/docker"

# 1. Pre-seed while legacy serves mail (already done above)

# 2. Maintenance window: stop legacy exim
docker stop exim

# 3. Rsync delta since pre-seed
rsync -aH --delete "$BASE/mail/" "$BASE/_migration_backup/cutover-$(date +%Y%m%d-%H%M%S)/mail/"

# 4. Import final delta
bash "$BASE/viswall/scripts/import_maildirs.sh" --run

# 5. Start Viswall mail-service
cd "$COMPOSE_DIR"
docker compose --profile mail up -d mail-service

# 6. Verify ports
for p in 25 465 587 110 143 993 995; do
  (exec 3<>/dev/tcp/127.0.0.1/"$p") 2>/dev/null && { echo "$p open"; exec 3>&-; } || echo "$p CLOSED"
done
```

## Phase 7: Post-Migration Verification

Check each item before declaring the migration complete:

- [ ] All expected domains appear in the Viswall admin console.
- [ ] A test user can log in via an IMAP client (Thunderbird, Apple Mail, etc.).
- [ ] A test user can send mail via SMTP AUTH.
- [ ] An inbound test mail arrives in the correct mailbox.
- [ ] Outbound mail from `example.com` carries a DKIM signature.
- [ ] SOGo webmail loads at `https://mail.example.com`.
- [ ] Quotas are enforced (if configured).
- [ ] Nightly backups are running (`borg list /backup/borg`).
- [ ] No port conflicts remain with the legacy container.

Useful verification commands:

```bash
CID=$(docker compose -f /opt/viswall/viswall/deployments/docker/docker-compose.yml ps -q mail-service)

# Auth test
docker exec "$CID" doveadm auth test user@domain 'password'

# Routing test
docker exec "$CID" exim4 -bt user@domain

# Queue depth
docker exec "$CID" exim4 -bpc

# DKIM check: look for "DKIM: d=example.com s=viswall" in mainlog
docker exec "$CID" tail -50 /var/log/exim4/mainlog

# SOGo health
curl -sSk -o /dev/null -w '%{http_code}\n' https://mail.example.com/
```

## Phase 8: Rollback (if needed)

If anything fails, run the rollback script:

```bash
bash /opt/viswall/viswall/scripts/rollback.sh
```

The script stops the Viswall `mail-service` and starts the legacy `exim` container. If the container is missing, it re-runs `start_exim.sh`. Ports return within seconds.

**Why rollback is safe:**

- The legacy data directories (`mysql/`, `mail/`, `log/`) were never modified; the import was read-only on source.
- No data loss occurs when reverting.

Roll back immediately if you see mail flow failures, widespread auth failures, or any sign of data corruption.

## Phase 9: Legacy Decommission (after soak period)

Wait at least 2-4 weeks of stable operation before removing the legacy stack.

1. Archive the legacy image tar, DB dump, and config off-host.
2. Remove the legacy container:

   ```bash
   docker rm exim
   ```

3. Remove legacy data directories **only after confirming archives are safe**:

   ```bash
   rm -rf /opt/viswall/mysql
   rm -rf /opt/viswall/mail
   rm -rf /opt/viswall/log
   ```

4. Remove `start_exim.sh` from any startup path.
5. Update documentation to reflect that the legacy stack is gone.
6. Restore DNS TTLs to normal values if they were lowered for cutover.

## Appendix A: Script Reference

| Script | Purpose | Key flags / examples |
|---|---|---|
| `scripts/migrate_legacy_mail.py` | ETL for domains, mailboxes, aliases, and quotas | `python scripts/migrate_legacy_mail.py --default-domain example.com --overrides _migration_backup/identity_overrides.tsv --commit` |
| `scripts/import_maildirs.sh` | Copy legacy maildirs into the `mail_data` volume | `bash scripts/import_maildirs.sh` (dry run); `bash scripts/import_maildirs.sh --run` |
| `scripts/cutover.sh` | Orchestrated maintenance-window cutover | `bash /opt/viswall/viswall/scripts/cutover.sh` |
| `scripts/rollback.sh` | Emergency rollback to legacy `exim` | `bash /opt/viswall/viswall/scripts/rollback.sh` |

## Appendix B: Configuration Mapping

| Legacy | Viswall |
|---|---|
| MariaDB `exim.Mailusers.Passwort` (cleartext) | Postgres `mail_users.password_hash` (bcrypt `$2b$`) |
| MariaDB `exim.Aliases` (`Email` → `Forwarder`) | Postgres `mail_aliases` (`source` → `destination`) |
| Courier IMAP/POP3 | Dovecot `imapd`/`pop3d`/`lmtpd` |
| Exim pgsql → MariaDB | Exim pgsql → Postgres |
| Courier authdaemon | Dovecot SASL (`/var/run/dovecot/auth-exim`) |
| `start_exim.sh --network host` | Docker Compose `--profile mail` |
| Courier Maildir | Dovecot Maildir++ (same format, UIDs preserved) |
| SpamAssassin + ClamAV | SpamAssassin + ClamAV inside `mail-service` |

## Appendix C: Troubleshooting

Common issues encountered during this migration:

- **SOGo auth fails:** `sogo_user_view` must map to `mail_users` JOIN `mail_domains`, not the admin `users` table. Fixed by Alembic migration `7383bc760d32`.
- **SOGo cannot reach IMAP:** the IMAP URL must use the trailing-slash form: `imap://mail-service:143/?tls=YES&tlsVerifyMode=none`. The ampersand-separated query string is parsed incorrectly without the slash.
- **nginx `proxy_buffer_size` too small:** SOGo session cookies exceed the default 4k. Raise to `128k` in the SOGo vhost.
- **SOGo blank page after monitor hits:** Roundcube-style `?_task=` URLs must be blocked at nginx (`return 302 /`) to prevent SOGo template-cache poisoning.
- **Dovecot quota unit:** use `*:bytes=<n>` not `*:storage=<n>`. The latter is interpreted in kilobytes and causes incorrect quota enforcement.
- **Container name mismatch:** the `sogo` container is named `viswall-sogo-1` because the compose project name is `viswall`. Use `docker compose ps` to confirm names before running `docker exec` or `docker cp`.
