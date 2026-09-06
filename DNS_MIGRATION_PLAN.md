# DNS Migration Plan: dns1 (BIND9/Webmin) → Viswall DNS Module

Status: **CUTOVER COMPLETE — 2026-09-06 07:12 UTC** (operator-approved).
dns1 is stopped (`restart=no`, retained for rollback; Webmin :10000 gone).
Production DNS on 46.4.63.216:53 is served by `viswall-dns-service-1`; all four
zones verified authoritative-correct (SOA/NS/MX/TXT/A/wildcard), recursion
REFUSED parity, heartbeat live, agent/rndc healthy. AXFR from non-secondary IPs
is denied by design (allow-transfer 93.111.66.28 only — same posture as dns1).
Rollback remains: `docker compose stop dns-service && docker update
--restart=always dns1 && docker start dns1` (from deployments/docker).

## ⚠ Post-cutover observation for the dns2 fix (operator-owned, decision Ad 1)
Public resolvers queried right after cutover return **stale data sourced from
dns2** (93.111.207.203): `wuehrer.me A → 85.208.168.3` (dns2's own IP) with
**TTL 300** — an old zone revision ($ttl 300, no wildcard → NODATA for random
names). dns2 times out from this host but evidently answers the internet
(source-filtered?). It is NOT slaved to dns1 (its config masters 10.40.201.10).
dns1/dns2 split-brain predates this migration (old and new dns1 serve identical
current data). Suggested fix path when handling dns2: re-slave it to
46.4.63.216 (TSIG available via console) or remove dns2.grafixpromo.com from
the zones' NS records via the viswall console.

## Remaining follow-ups
- Soak (Phase 6): monitor `docker logs viswall-dns-service-1`, agent
  `/dns/status`, console audit log for ≥2 weeks.
- Commit branch `feat/dns-service-production` (awaits operator go).
- Decommission dns1 (Phase 8) after soak: `docker rm dns1`, keep
  `/data/docker/persistent/dns1` + `backup/dns1-20260905-2133.tgz` for 6 months.

---

## Implementation record (what shipped)
- `services/dns-service/viswall_dns_agent/` — package replacing single-file agent:
  options/zones split across `named.conf.options` + `named.conf.local`
  (fixes duplicate-options abort), `listen-on`/`listen-on-v6` rendering with
  wildcard→`any` normalization, server-level `also-notify`, `dnssec-validation`
  derived from recursion (avoids distro-default crash loop without root path),
  X-Instance-Key auth on all mutating endpoints, gateway heartbeat loop.
- `services/dns-service/{Dockerfile,entrypoint.sh,supervisord.conf}` — named
  (user bind) + agent under supervisord; rndc key/conf handling
  (`rndc.conf` does NOT support `include`; distro key name is `rndc-key`).
- `services/api-gateway/utils/agent_client.py` — per-service endpoints via
  `Instance.config["agent_endpoints"][service]` + `X-Instance-Key` header.
- `services/api-gateway/utils/dns_dispatch.py` — composes full instance desired
  state (all enabled servers merged; BIND = one options block per host), pushes
  `/dns/apply`, marks server running/error.
- `services/api-gateway/routers/dns.py` — background dispatch on every mutation;
  `actions/apply` (sync), `actions/reload` (agent rndc), start triggers apply.
- `deployments/docker/docker-compose.yml` — dns-service enabled: bridge network
  `viswall`, publish `${DNS_PUBLISH_ADDR:-46.4.63.216}:${DNS_PUBLISH_PORT:-53}:53`,
  agent API loopback-only `127.0.0.1:8082`, volumes `dns_bind_etc`/`dns_bind_lib`,
  `cap_add: NET_BIND_SERVICE`.
- `scripts/migrate_legacy_bind.py` — dnspython-based importer (dry-run default,
  `--apply`); preserves SOA (mname/rname/serial), splits MX/SRV priority fields,
  keeps auto system-NS for the server name, `--listen 0.0.0.0` for bridge mode.
- Console state: server id=3 (dns1.grafixpromo.com, recursion off,
  allow-transfer/also-notify 93.111.66.28, listen 0.0.0.0) + 4 zones + records.
  Instance 1 `agent_endpoints.dns = http://dns-service:8082`, api_key aligned
  with `.env` `INSTANCE_API_KEY`.
- Tests: agent 20 (render/auth), gateway 43 (incl. 6 new dispatch tests);
  conftest isolates unit tests from real agent/DB.

## Lessons baked into code/config (do not regress)
- Bridge-mode containers MUST listen `0.0.0.0` inside the namespace; the compose
  publish pins the external address.
- `listen-on`/`listen-on-v6` changes require a named restart (`rndc reload` won't
  re-bind); restart dns-service after changing listening_addresses.
- `rndc reload` exits 0 even when zones fail to load — verify with dig, not rc.

## Cutover runbook (Phase 5 — EXECUTED 2026-09-06 07:12 UTC)
```bash
cd /data/docker/persistent/exim4/viswall/deployments/docker
docker update --restart=no dns1 && docker stop dns1          # Webmin :10000 dies too
DNS_PUBLISH_ADDR=46.4.63.216 DNS_PUBLISH_PORT=53 docker compose up -d dns-service
for z in hybridz.net triolog.media visionsinmind.com wuehrer.me; do
  dig +short @46.4.63.216 $z SOA
done
# external spot-check: wuehrer.me A + MX from a public vantage point
```
Rollback:
```bash
DNS_PUBLISH_PORT=1053 docker compose up -d dns-service   # or stop it
docker update --restart=always dns1 && docker start dns1
```
Phase 2 backup: `/data/docker/persistent/backup/dns1-20260905-2133.tgz` (+ image ref).

---

## Original assessment (kept for reference)

Verdict: **Migration is feasible** with a small amount of module hardening first.
The dns module (BIND9 + agent) and the console (live at
https://viswall.webmasters.co.at) are functionally present, but the agent is not
production-ready as-is and the console never pushes config to it. Both gaps are
small, well-scoped, and listed in Phase 1.

---

## 1. Current State (inventory, verified 2026-09-05)

### dns1 container

| Item | Value |
|---|---|
| Image | `sameersbn/bind:latest` (BIND9 + Webmin) |
| Launcher | `/data/docker/persistent/dns1/start_dns1` (`docker run -d --restart=always`) |
| Ports | `46.4.63.216:53/udp`, `46.4.63.216:53/tcp`, `0.0.0.0:10000` (Webmin) |
| Data | `/data/docker/persistent/dns1` → `/data` (bind etc+lib, webmin) |
| Zones (master) | `hybridz.net`, `triolog.media`, `visionsinmind.com`, `wuehrer.me` (~8–17 lines each, Webmin-managed) |
| Zone serials | `2024031201` (x3), `2014081711` (visionsinmind.com) |
| Transfers | `allow-transfer { 93.111.66.28; }`, `also-notify { 93.111.66.28; }` per zone |
| Recursion | **REFUSED** for recursive queries (authoritative-only in practice) |
| DNSSEC | Zones unsigned; `dnssec-validation auto` (irrelevant while recursion is refused) |

Zone template (wuehrer.me): SOA `dns1.grafixpromo.com. admin.webmasters.co.at.`,
NS `dns1/dns2.grafixpromo.com.`, MX 10/20 `mx1/mx2.webmasters.co.at.`, SPF TXT,
A + wildcard A → `85.208.168.4`. `$ttl 38400`.

### Environment / dependencies

- This host **is** `46.4.63.216` (= `node0.webmasters.co.at` = `dns1.grafixpromo.com`).
- Host resolution uses systemd-resolved → Hetzner resolvers (185.12.64.1/2). **No host dependency on dns1.**
- No other container uses dns1 as resolver (only dns1 itself uses 127.0.0.1).
- **Remote secondary `dns2.grafixpromo.com` (93.111.207.203) is unreachable (query timeouts)** although all four zones still list it in NS. Pre-existing issue, must be decided on (see Open Decisions).
- Local `/data/docker/persistent/dns2` is a **stale copy** of a slave config from an old setup (masters 10.40.201.10); the real dns2 runs on a remote host. Not part of this migration.
- `webmasters.co.at` zone itself is **not** hosted on dns1 → no chicken-and-egg problem for `viswall.webmasters.co.at` during cutover.

### Viswall console (already deployed on this host)

- Stack (compose project `viswall`, working dir `/data/docker/persistent/exim4/viswall/deployments/docker`):
  `api-gateway` (127.0.0.1:8010→8000, healthy), `web-ui` (127.0.0.1:8088→80),
  `postgres` (127.0.0.1:5432), `redis`, `mail-service`, `sogo`, `grafana`, `prometheus`, `ollama`.
- Public endpoint: https://viswall.webmasters.co.at (host nginx, TLS LE) → web-ui / api-gateway. Verified HTTP 200.
- Instance registry: instance **id=1 "Local"** exists, status active, capabilities already include `"dns"`.
- `INSTANCE_API_KEY` is present in `deployments/docker/.env`.
- Web UI has DNS pages (`web-ui/src/pages/DNS/`); gateway DNS API mounted at `/api/v1/dns`.

---

## 2. Target Architecture

```
Internet ──53/tcp+udp──> 46.4.63.216 (this host)
                          └─ viswall dns-service container (bridge net)
                             ├─ named (BIND9, ubuntu:24.04)   — authoritative, recursion off
                             └─ dns_agent.py (FastAPI :8082, loopback-published only)
Console: https://viswall.webmasters.co.at (web-ui + api-gateway + postgres)
         └─ CRUD /api/v1/dns/*  ──(new: agent dispatch via agent_client.py)──> 127.0.0.1:8082/dns/apply
```

- Management moves from Webmin (:10000, dies with dns1) to the viswall console.
- Data plane keeps serving from the same IP/port, so client/cache impact is ~zero (NS records and IPs unchanged).
- Zone data becomes console-owned (Postgres) and is rendered to BIND files by the agent
  (`zone-{id}-{name}.db` under `/var/lib/bind/viswall-zones`, generated `named.conf.local`).

---

## 3. Module Gaps That Must Be Closed First (Phase 1 work)

Verified in code on both the deployed branch and upstream main (`ec64559`) —
`services/dns-service/` is identical on both:

1. **named is never started.** `Dockerfile` CMD is only `python3 dns_agent.py`.
   Need an entrypoint that runs `named` (foreground, `-u bind`) **and** the agent.
2. **Duplicate `options {}` bug.** Agent writes an `options{...}` block into
   `/etc/bind/named.conf.local`, but Ubuntu's stock `/etc/bind/named.conf` already
   includes `named.conf.options` → `options redefined` → named won't start.
   Fix: point `NAMED_CONF_PATH` at a viswall-owned file and run `named -c` against a
   minimal main config that includes only that file (or split options into
   `named.conf.options`).
3. **No auth on the agent API (:8082).** `INSTANCE_API_KEY`/`GATEWAY_URL` env vars
   are set in compose but **never read** by `dns_agent.py`. Anyone reaching 8082 can
   rewrite DNS. Fix: add API-key check middleware + publish `127.0.0.1:8082:8082` only
   (never `0.0.0.0` as the commented compose block suggests).
4. **Gateway→agent dispatch missing for DNS.** `routers/dns.py` is pure CRUD;
   `server_action`/`sign_zone` are mocked (confirmed by repo's own `gap_analysis.md`).
   `utils/agent_client.py` (httpx, added in #48) already wires firewall/mail/vpn —
   DNS needs the same treatment: after any mutation, compose `DNSServerConfigPayload`
   from DB and POST to the instance agent `/dns/apply`. Add agent heartbeat
   (`POST /api/v1/instances/1/heartbeat` with `INSTANCE_API_KEY`) so the console shows liveness.
5. **Compose block bugs.** `network_mode: host` + `ports:` is contradictory, and
   `GATEWAY_URL: http://api-gateway:8000` doesn't resolve from host network. Use
   bridge networking + `46.4.63.216:53:53/udp+tcp` port publishing (mirrors dns1 today),
   `GATEWAY_URL: http://172.x.y.z|host-gateway:8010` or loopback, and
   `cap_add: [NET_BIND_SERVICE]`.
6. **No persistence volume** for `/etc/bind` + `/var/lib/bind` in the compose block — add one.
7. **Known limitations to document, not fix now:**
   - DNSSEC in the module is synthetic (no real `dnssec-keygen`/RRSIG). Keep
     `dnssec_enabled=false` for all zones (they are unsigned today anyway). File an upstream issue.
   - Per-zone plain-IP `allow-transfer`/`also-notify` aren't rendered (only TSIG-key ACLs).
     Current per-zone ACL is a single IP (93.111.66.28) → replicate via the server-level
     `allow_transfer` list. `also-notify` is dropped (secondary is dead — see Open Decisions).

---

## 4. Phased Plan

### Phase 0 — Repo prep (½ h)
1. Sync checkout with upstream main (`ec64559` or later); create branch
   `feat/dns-service-production` from it. Do **not** touch the running compose project
   until Phase 4 (running stack is on the old branch; rebuild only the new service).
2. Confirm `git status` clean; note that no upstream changes to `services/dns-service/` exist
   (verified: identical main↔branch).

### Phase 1 — Module hardening + console wiring (1–2 days)
Changes (all in the viswall repo, with tests):
1. `services/dns-service/entrypoint.sh`: start `named -g -u bind -c <conf>`, wait for
   :53, then exec agent. `chown bind:bind` zones/keys dirs.
2. `dns_agent.py`:
   - read `INSTANCE_API_KEY`, require it as `X-Instance-Key` header on all mutating endpoints;
   - fix options-duplication (write into a viswall-owned included file);
   - optional: emit `also-notify` for plain IPs (small patch, enables future secondary).
3. `routers/dns.py` + `utils/agent_client.py`: after server/zone/record/TSIG mutations,
   dispatch full `DNSServerConfigPayload` to the instance agent (`/dns/apply`), using the
   same pattern as firewall/mail/vpn (#48). Failure → 502 + audit log entry, DB keeps desired state.
4. Heartbeat loop in agent (every 30 s → `/api/v1/instances/1/heartbeat`) so instance
   `last_seen`/status stay green in the console.
5. Compose: real `dns-service` block — bridge network, `46.4.63.216:53:53/udp+tcp`,
   `127.0.0.1:8082:8082`, `cap_add: NET_BIND_SERVICE`, volume for `/var/lib/bind`
   (+`/etc/bind`), `DNS_AGENT_ALLOW_COMMANDS: "true"`, `restart: unless-stopped`.
6. Unit tests: agent payload→file rendering (incl. wildcard/MX/SPF), header auth,
   gateway dispatch happy/unreachable path. Run `pytest services/api-gateway/tests`.

Acceptance: local `docker compose up dns-service` on a test port answers authoritative
queries for a dummy zone pushed from the console UI end-to-end.

### Phase 2 — Cold backup (15 min)
```bash
STAMP=$(date +%Y%m%d-%H%M)
tar -C /data/docker/persistent -czf /data/docker/persistent/backup/dns1-$STAMP.tgz dns1/
docker exec dns1 dnssec-keygen --version >/dev/null 2>&1 # noop; capture image tag:
docker inspect dns1 --format '{{.Config.Image}} {{.Image}}' > /data/docker/persistent/backup/dns1-$STAMP.image
```
dns1 keeps serving throughout.

### Phase 3 — Data migration into console (½ day)
1. New script `scripts/migrate_legacy_bind.py` (model: `migrate_legacy_mail.py`):
   - parse the four Webmin `.hosts` files from `/data/docker/persistent/dns1/bind/lib/`
     (dnspython zone parsing; they are standard master files with `$ttl`);
   - `POST /api/v1/dns/servers/1` — create server:
     `listening_addresses ["46.4.63.216"]`, `port 53`, `is_recursive false`,
     `is_authoritative true`, `allow_query ["0.0.0.0/0","::/0"]`,
     `allow_transfer ["93.111.66.28"]`, no forwarders;
   - per zone: `POST /api/v1/dns/servers/{server_id}/zones` (keep SOA values; console
     auto-serial `YYYYMMDDHH` > `2024031201` ✓); include existing SOA as a record to
     preserve `dns1.grafixpromo.com.`/`admin.webmasters.co.at.` (default would be `ns1.<zone>`);
   - records via `POST /api/v1/dns/zones/{zone_id}/records/bulk` (≤500/call — total is ~40 records);
   - dry-run mode printing the payload diff; `--apply` to execute.
2. Verify in console UI: 4 zones, record counts, SOA/NS/MX/TXT/wildcard A.
3. Do **not** apply to the live agent yet (dns1 still owns :53).

### Phase 4 — Parallel validation (½ day, no downtime)
1. Start `dns-service` with test port publish (e.g. `46.4.63.216:5353`).
2. Apply config from console; check:
   - container logs: named started, zone files loaded, `rndc status` OK;
   - `named-checkzone <zone> <file>` per zone inside the container;
   - **record-by-record diff** old vs new:
     ```bash
     for z in hybridz.net triolog.media visionsinmind.com wuehrer.me; do
       diff <(dig +noall +answer @46.4.63.216 $z AXFR) \
            <(dig +noall +answer @46.4.63.216 -p 5353 $z AXFR)
     done
     ```
     (AXFR is allowed from localhost on both.) Plus explicit checks: SOA serial >
     old, MX priorities, TXT SPF string, wildcard `*.wuehrer.me` A, REFUSED for
     recursive queries (parity: `dig @new -p 5353 example.com` → REFUSED).
3. Re-run after a second console-side edit (e.g. TTL change → revert) to prove the
   full round-trip incl. `rndc reload`.

### Phase 5 — Cutover (10 min window, ~zero client impact — same IP)
1. `docker update --restart=no dns1 && docker stop dns1`
2. Repoint dns-service ports to `46.4.63.216:53:53/{tcp,udp}` and start it
   (`docker compose up -d dns-service`).
3. Immediate checks: `dig @46.4.63.216 <zone> SOA` for all 4 zones; external vantage
   point query (e.g. from phone/external host) for `wuehrer.me A` and `MX`.
4. Webmin on :10000 disappears with dns1 — expected; management is now the console.

### Phase 6 — Post-migration verification (day 1)
- Monitor `docker logs`, `rndc status` via agent `/dns/status`, console audit log.
- External checks: all 4 zones resolve from a public resolver; SOA serials current.
- Make one trivial record edit via console UI and confirm propagation (proves day-2 operability).

### Phase 7 — Rollback (if anything fails)
```bash
docker compose stop dns-service     # or: docker update --restart=no viswall-dns-service-1 + stop
docker update --restart=always dns1 && docker start dns1
dig @46.4.63.216 wuehrer.me SOA     # expect 2024031201
```
Zone data on dns1 was never modified — rollback is exact. Console keeps the imported
data (harmless; reused on next attempt).

### Phase 8 — Decommission (after ≥2 weeks soak)
- Keep the Phase-2 tarball; remove dns1 container (`docker rm dns1`) and optionally
  `/data/docker/persistent/dns1` (recommend: keep 6 months).
- Resolve the secondary question (Open Decision 1): either restore a working
  secondary (dns2 or a viswall slave zone via TSIG — module supports it) and keep both
  NS records, or remove `dns2.grafixpromo.com.` NS records from the four zones via console.

---

## 5. Open Decisions (needed before Phase 1)

1. **Dead secondary**: `dns2.grafixpromo.com` (93.111.207.203) times out but is still
   in every zone's NS. Fix it, replace it, or drop the NS records? (Recommend: drop NS
   entries at cutover — one NS is honest; revisit when a second node exists.)
2. **Console wiring scope**: implement gateway→agent dispatch + heartbeat in the repo
   (recommended, ~1–2 days, benefits all future nodes) vs. minimal manual
   `curl POST /dns/apply` bridge for now.
3. **Branch**: land Phase-1 work on a branch off upstream `main` and redeploy the
   console from it, vs. continue on `feat/mailserver-hardening-and-sogo`. (Recommend:
   new branch off main; console redeploy is a normal rolling restart.)
4. **SOA admin contact**: keep `admin.webmasters.co.at.` (current) for all zones.

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Agent rendering bug breaks a zone | Med | Med | Phase 4 AXFR diff before cutover; named-checkzone |
| Duplicate-options / named startup failure | High (if unpatched) | High | Phase 1 fix + staging on :5353 |
| :8082 exposed unauthenticated | High (if unpatched) | High | Loopback bind + API key (Phase 1.3) |
| Dead secondary causes long negative-cache/NS issues | Low | Low | It's already dead; NS cleanup at cutover |
| Console DB loss after cutover | Low | High | DNS files persist in agent volume; pg_dump in existing backup routine; zones re-importable |
| Rollback needed | Low | Low | dns1 untouched until Phase 8; exact-state rollback in minutes |

## 7. Effort Summary

| Phase | Effort |
|---|---|
| 0 Repo prep | ½ h |
| 1 Module hardening + wiring | 1–2 d |
| 2 Backup | 15 min |
| 3 Import script + run | ½ d |
| 4 Parallel validation | ½ d |
| 5 Cutover | 10 min |
| 6–8 Verify / soak / decommission | 2 weeks calendar |

Total hands-on: ~2.5–3.5 days, of which ~1–2 days are reusable upstream work on the
viswall dns module itself.
