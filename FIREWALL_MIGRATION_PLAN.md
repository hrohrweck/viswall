# Firewall Migration Plan: boseman iptables legacy stack → Viswall firewall module

Status: **PLANNED, NOT EXECUTED**. Skeleton written 2026-10-22. This document is the
migration's source of truth and is followed verbatim during todos 38-48 of
`.omo/plans/firewall-migration.md`, then corrected wherever reality diverges.

Host: `boseman` / `46.4.63.216` (Hetzner KVM, single NIC `enp0s31f6`).
Console: `https://viswall.webmasters.co.at`.
Repo branch: `feat/firewall-production` in `/data/docker/persistent/viswall/viswall-fwdev`.
Model: `DNS_MIGRATION_PLAN.md` (structure and cutover-record style).

The goal: the viswall console becomes the single management surface for firewall
rules, NAT, routing, QoS, interfaces (including netplan IP config) and the existing
WireGuard site-to-site client, while every currently open port, rate limit and
internal-port protection stays byte-for-byte equivalent, and Docker keeps owning its
own tables and chains.

**Safety rails that apply to every phase**

- Port 22 stays open, key auth only, and the hashlimit is preserved verbatim.
- WireGuard 51820/udp stays open and the tunnel stays a split tunnel on `10.80.0.0/16`.
- No `flush ruleset` anywhere, at any time, by any script or agent.
- No changes to mail, DNS, or any hosted workload's runtime config.
- No edits under `/opt/viswall` (CD-owned checkout).
- No push to `main`; one PR from `feat/firewall-production`.
- Every risky step runs behind the watchdog and revert trap described in section 4.
- The legacy rules stay archived and restorable for at least 6 months.

## Source data (all numbers below trace to these files)

| Source | Path | What it proves |
| --- | --- | --- |
| Live IPv4 capture | `/data/docker/persistent/backup/firewall-20261022-221901/rules.v4.live` | live `iptables-save`, 2026-10-22 22:21:09 UTC, 23,579 B |
| Live IPv6 capture | `/data/docker/persistent/backup/firewall-20261022-221901/rules.v6.live` | live `ip6tables-save`, 2026-10-22 22:21:10 UTC, 9,019 B |
| Live nft dump | `/data/docker/persistent/backup/firewall-20261022-221901/nft-ruleset.live` | 39,778 B, iptables-nft compat tables only |
| Evidence record | `.omo/evidence/task-3-firewall-migration.md` | backup inventory, hashes, restore proof |
| Evidence record | `.omo/evidence/task-1-firewall-migration.md` | generator hunt, live-vs-file divergence |
| Evidence record | `.omo/evidence/task-5-firewall-migration.md` | instance-1 row and heartbeat proof |

The cold backup is authoritative for the legacy world:
`/data/docker/persistent/backup/firewall-20261022-221901.tar.gz`, 1,090,147 bytes,
147 tar entries, SHA256 `c98ac33051de461fd5999cc6654b3f0ae2d3c59f86e94e036f085f3b62bc2dff`.
Restore proof against a scratch database: live `instances` count = 1, restored count = 1.
The cutover itself must take a **fresh** snapshot inside the window (Docker NAT/DNAT
drift with container lifecycle); the cold backup is the rollback floor, not the
cutover source.

---

## 1. Current-state inventory (live capture, 2026-10-22 22:21 UTC)

### 1.1 IPv4 input policy and open ports

Filter table policies: `INPUT DROP`, `FORWARD DROP`, `OUTPUT ACCEPT`.

| Port / proto | Action | Rate limit (per source IP) | Capture line |
| --- | --- | --- | --- |
| 22/tcp | ACCEPT | `ssh_limit`: drop above 10/min, burst 5 | 80-81 |
| 25/tcp | ACCEPT | none | 82 |
| 53/udp | ACCEPT | none | 83 |
| 53/tcp | ACCEPT | none | 84 |
| 80/tcp | ACCEPT | `http_limit`: drop above 100/min, burst 5 | 89-90 |
| 110/tcp | ACCEPT | none | 85 |
| 143/tcp | ACCEPT | none | 86 |
| 443/tcp | ACCEPT | `https_limit`: drop above 100/min, burst 5 | 91-92 |
| 993/tcp | ACCEPT | none | 87 |
| 995/tcp | ACCEPT | none | 88 |
| 51820/udp | ACCEPT | `wireguard_limit`: drop above 20/min, burst 5 | 93-94 |
| 21114/tcp | ACCEPT | none | 98 |
| 21115/tcp | ACCEPT | none | 99 |
| 21116/tcp | ACCEPT | none | 100 |
| 21116/udp | ACCEPT | none | 101 |
| 21117/tcp | ACCEPT | none | 103 |
| 21118/tcp | ACCEPT | none | 102 |
| 21119/tcp | ACCEPT | none | 104 |

Ordering in the live INPUT chain, which the renderer must preserve:

1. `-m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT` (line 78).
2. `-i lo -j ACCEPT` (line 79).
3. The four hashlimit DROP rules, each immediately before its matching ACCEPT.
4. `-m limit --limit 5/min -j LOG --log-prefix "FIREWALL-DROP: "` (line 95).
5. `-i docker0 -j ACCEPT` (line 96). Docker-owned, must survive the migration.
   `docker0` is the **only** bridge with a broad INPUT accept: the live capture
   has no `br-*` accept, so bridge-to-host traffic on every other bridge falls
   to the INPUT policy `DROP` exactly like live. The renderer adds no broad
   `br-*` input accept; its only `br-*` accepts are the port-scoped
   agent-control accepts (8081/8083/8085, a viswall-only addition with no live
   equivalent, parity row A35).
6. `-p tcp --dport 5432 -j DROP` (line 97). Postgres is never reachable from the public NIC.
7. RustDesk accepts, 21114-21119 tcp plus 21116 udp (lines 98-104).

Everything not matched falls through to the INPUT policy `DROP`. Live counter at
capture: `INPUT DROP [5273045:297019817]`.

The four hashlimit DROP rules render as port-scoped nft meters with the **`over`**
keyword, e.g. `tcp dport 22 meter ssh_limit { ip saddr limit rate over 10/minute
burst 5 packets } drop` (http/https 100/minute, wireguard 20/minute, one bucket per
family). The `over` keyword is mandatory: a plain `limit rate N/minute` accepts the
under-rate traffic and inverts the hashlimit drop into an allow. Meters must keep
the single `burst` clause (a duplicated burst makes `nft -f` fail).

### 1.2 IPv6 input (narrower by design)

`INPUT DROP`, `FORWARD DROP`, `OUTPUT ACCEPT`. Open: 22/tcp with `ssh_limit_v6`
(10/min, burst 5), 80/tcp with `http_limit_v6` (100/min, burst 5), 443/tcp with
`https_limit_v6` (100/min, burst 5), 51820/udp with `wireguard_limit_v6`
(20/min, burst 5). Also `-i docker0 -j ACCEPT` and the same FIREWALL-DROP log rule.
IPv6 does **not** inherit the IPv4 mail, DNS or RustDesk accepts. Mail and DNS are
IPv4-only in the live capture.

Capture also contains 15 IPv6 raw anti-spoof drops for container addresses on
`br-dcbbead2b63e` (`fd00:42::`) and `docker0` (`2001:db8:1::`), plus the same 17
DOCKER-USER internal-port drops as IPv4.

### 1.3 DOCKER-USER internal-port protection (17 ports)

Lines 206-222 of `rules.v4.live`, one drop per port, all shaped as
`-A DOCKER-USER -i enp0s31f6 -p tcp -m conntrack --ctorigdstport <PORT> --ctdir ORIGINAL -j DROP`:

`5000, 5055, 5678, 8000, 8001, 8080, 8089, 8090, 8091, 8096, 8100, 8201, 8502, 8888, 9090, 10000, 11434`

This is the protection that currently blocks direct public access to container
ports that happen to be DNATed. The viswall renderer replaces it with one named
rule, `docker-internal-port-protection`, in the viswall forward chain, using this
exact list taken from the live capture (never a hardcoded list in code).

### 1.4 Raw anti-spoof and loopback guards (60 v4 rules)

`*raw` PREROUTING contains 60 drop rules on IPv4 (plus the 15 IPv6 container-IP
drops noted in 1.2):

- **63 container-IP anti-spoof rules (48 IPv4 + 15 IPv6)**, one per live
  container address across 13 bridges: `-A PREROUTING -d <container-ip>/32 ! -i <bridge> -j DROP`.
  Example: `-d 172.19.0.2/32 ! -i br-dcbbead2b63e -j DROP`. These render in the
  viswall **`raw_prerouting` chain (filter hook prerouting priority -300, pre-DNAT)**
  as `iifname != "<bridge>" ip daddr <container-ip> drop`, generated from the live
  capture. The placement is pre-DNAT on purpose: docker DNATs WAN-published ports to
  the container IP before the forward hook, so a forward-chain placement matches the
  DNAT'd published flows and drops every WAN-published port (netns-proven in todo
  39b: WAN->:25 published flow rc=1 with the forward placement, rc=0 with
  `raw_prerouting`). They must not render in FORWARD and must not render in INPUT
  (those packets are forwarded, not locally delivered).
- **12 loopback guards**, `-A PREROUTING -d 127.0.0.1/32 ! -i lo -p tcp --dport <PORT> -j DROP`
  for `3000, 3001, 5432, 6379, 8010, 8065, 8082, 8088, 8095, 9091, 9121, 20000`.
  These are imported as INPUT rows, and the renderer hoists them into the same
  `raw_prerouting` (pre-DNAT) chain: docker DNATs the 127.0.0.1-published ports
  before the input hook, so the input hook would never see those flows. The guard
  is what stops them, pre-DNAT, exactly like live (parity row A32); it never renders
  in the input or forward chain.

### 1.5 Docker-owned NAT and the duplicate pileup

The `*nat` table is entirely Docker's: `DOCKER` DNAT rules per published port,
`DOCKER-ISOLATION-*` style chains in the filter table, and the `POSTROUTING`
masquerade rules. None of it is imported as viswall NAT.

Live counts at capture:

- 65 `MASQUERADE` lines total.
- 19 distinct masquerade shapes.
- **48 identical copies** of `-A POSTROUTING -s 172.17.0.0/16 -o enp0s31f6 -j MASQUERADE`
  (47 plain plus one carrying the comment `Allow Docker NAT for internet access`).
  This is the documented duplicate pileup. It is Docker's to own and will reappear
  after a Docker restart or network recreate. It is not a migration regression.

### 1.6 Netplan (WAN configuration)

`/etc/netplan/01-netcfg.yaml` (Hetzner installimage, mode 0600):

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp0s31f6:
      addresses:
        - 46.4.63.216/32
        - 2a01:4f8:140:22ef::2/64
      routes:
        - on-link: true
          to: 0.0.0.0/0
          via: 46.4.63.193
        - to: ::/0
          via: fe80::1
      nameservers:
        addresses:
          - 185.12.64.1
          - 2a01:4ff:ff00::add:2
          - 185.12.64.2
          - 2a01:4ff:ff00::add:1
```

The WAN address is a `/32` on-link route, so a bad netplan write can strand the
host completely. Netplan is owned by the **node-agent** (port 8085), not the
firewall agent. Every apply goes through `netplan try --timeout 120` with health
probes and the 120 s auto-revert. Before writing, the node-agent copies the
previous file to `$STATE_DIR/backups/<utc-stamp>/` (`$STATE_DIR` defaults to
`/var/lib/viswall-node`), never to a backup directory inside `/etc/netplan`,
which netplan would parse as a second source. Automated WAN address changes are
out of scope (section 6).

### 1.7 WireGuard client (site-to-site, split tunnel)

Interface `client`, managed by the host unit `wg-quick@client`.

| Item | Value |
| --- | --- |
| Local address | `10.80.210.2/24` |
| Peer endpoint | `base0.webmasters.co.at:51820` (live `wg show` showed `188.45.201.39:51820`) |
| AllowedIPs | `10.80.0.0/16` (split tunnel, not a default route) |
| PersistentKeepalive | `25` |
| Local listening port | `40156` |
| Handshake at capture | 40 seconds old |
| Transfer at capture | 15.21 GiB received, 338.75 GiB sent |

No key material is reproduced in this document. Note for decommission: the backup
capture recorded `/etc/wireguard/client.conf` as mode 0644 (world readable) while
the directory is 0700. Hardening to 0600 happens at todo 49 through the VPN agent's
file-write path, with the tunnel verified up afterwards.

### 1.8 Docker interference symptoms (why the old agent could not be used)

1. **Native nftables cannot express this host's live rules.** `nft -c -f nft-ruleset.live`
   exits 1 on 20 `xt target MASQUERADE/DNAT` lines ("unsupported xtables compat
   expression"). `nft list tables` shows only `ip raw/filter/nat` and `ip6 raw/filter/nat`
   compat tables. There is no native nft table today. The restore path on this host
   is `iptables-restore`, not `nft -f`.
2. **Live rules and persisted files disagree.** `/etc/iptables/rules.v4` is 8,769 B
   (mtime 2026-09-01 21:37) while the live capture is 23,579 B. Live has the
   `DOCKER-FORWARD` chain, 13 bridges, 65 masquerade lines and 60 raw PREROUTING
   rules. The persisted file does not. Import must read the live capture, never
   the file.
3. **The 48 duplicate MASQUERADE lines** are evidence of repeated re-appends for the
   same docker0 subnet rule. Docker recreates NAT on daemon restart and network
   recreate, so duplicates return. Plan for that, do not "fix" it in viswall.
4. **Container lifecycle drift.** Any container restart after the capture changes
   the NAT/DNAT picture. This is why the cutover uses a fresh snapshot taken inside
   the window.
5. **The dump is Docker-managed.** It contains the marker
   `table ip filter is managed by iptables-nft, do not touch!`. The new firewall
   must live in its own table and never flush, delete or rewrite Docker's tables.

---

## 2. Target architecture

```
                    Internet
                       |
         46.4.63.216:22/25/53/80/110/143/443/993/995/21114-21119, 51820/udp
                       |
                enp0s31f6 (netplan-owned WAN, /32 + gw 46.4.63.193)
                       |
        +--------------+-----------------------------------------------+
        |                        Linux kernel                          |
        |                                                              |
        |  nftables                                                    |
        |  +---------------------------+   +-------------------------+ |
        |  | table inet viswall        |   | iptables-nft tables     | |
        |  |  input   hook -200 DROP   |   |  ip filter (Docker)     | |
        |  |  forward hook -150 DROP   |   |   DOCKER, DOCKER-USER,  | |
        |  |  output  hook -200 ACCEPT |   |   DOCKER-FORWARD,       | |
        |  |  nat (v1: empty)          |   |   DOCKER-ISOLATION-*    | |
        |  +---------------------------+   |  ip nat (DNAT/MASQ)     | |
        |                                  |  ip raw (compat)        | |
        |                                  +-------------------------+ |
        |                                                              |
        |  wg-quick@client  (single lifecycle owner of the tunnel)     |
        +--------------+-----------------------------------------------+
                       |
     host-bridge control plane (bridge-scoped INPUT accepts, X-Instance-Key auth)
                       |
   +-------------------+--------------------+
   |                                        |
viswall-firewall-service-1            viswall-vpn-service-1
(network_mode host, privileged,       (network_mode host, privileged,
 pid host, :8081 AGENT_HOST=0.0.0.0)   pid host, :8083 AGENT_HOST=0.0.0.0)
 volumes:                              volumes:
  /var/lib/viswall-firewall             /var/lib/viswall-vpn
  (nft state only)                      /etc/wireguard (rw, backed up)

viswall-node-agent-1 (network_mode host, :8085)
 volumes: /etc/netplan (rw); state: $STATE_DIR/backups (netplan try backups)
                       |                                        |
                       +----------------+-----------------------+
                                        |
                          api-gateway 127.0.0.1:8010
                          utils/agent_client.py
                          Instance.config.agent_endpoints[firewall|vpn|node]
                          header X-Instance-Key
                                        |
                          web-ui + Postgres  (console)
                          https://viswall.webmasters.co.at
```

Key properties:

- **Separate table, no flush.** `table inet viswall` is created and replaced by
  `nft delete table inet viswall` (ignore "no such table") followed by
  `nft -f ruleset.nft`. Docker's `ip`/`ip6` tables and chains are never touched.
- **Hook priorities.** input `-200`, forward `-150`, output `-200` (policy accept).
  Docker's iptables-nft filter sits at priority 0, so viswall input and forward
  policy runs first; Docker's chains still run afterwards for bridge traffic.
  NAT chains render at prerouting `-110` and postrouting `90`, but are empty in v1.
- **Dispatch.** Console mutation → gateway composes full desired state → POST
  `/firewall/apply` or `/vpn/apply` to the host-net agent with `X-Instance-Key`
  (the gateway runs in a bridge network, so instance-1 endpoints use
  `http://host.docker.internal:8081/8083/8085`, not guest loopback). The agent
  snapshots, renders, validates (`nft -c -f`), then applies.
  **Key-transit posture (F2 review #14, accepted as-is): the instance API key
  and every agent payload travel in CLEARTEXT over HTTP
  (`http://host.docker.internal:<port>`), with the agents bound to `0.0.0.0`
  via `AGENT_HOST`, with no TLS on the agent control plane. This is an accepted,
  documented posture: the transport never leaves the host (docker bridge to
  host), and the mitigations are the port-scoped INPUT accepts for the agent
  ports on `docker0`/`br-*` only (parity row A35), `X-Instance-Key` auth on
  every endpoint except `/health`, and no published agent ports. Anyone already
  able to sniff the host's bridge is root-equivalent anyway.**
- **Heartbeat.** Each agent posts `{"api_key": ..., "status": "ok"}` to
  `POST http://127.0.0.1:8010/api/v1/instances/1/heartbeat` so the console shows
  liveness. Auth is on the request body for this route (section 10).
- **Host equivalence is accepted risk.** The agents are privileged with host
  networking because they must run `nft`, `tc`, `ip`, `nsenter`, and (node-agent
  only) `netplan try`. Mitigations: `X-Instance-Key` auth on every endpoint
  except `/health`, minimal images, no published ports, and the port-scoped
  bridge reads described in the renderer facts below.
- **Renderer ordering facts (verified against `nft.py` and netns).**
  - Blacklist drops sit at the TOP of the input chain, immediately after
    `ct state established,related accept`, so a blocked source IP reaches no
    host INPUT service, including ports that are otherwise open.
  - The broad Docker INPUT accept is `docker0` only. The sole `br-*` INPUT
    accepts are the port-scoped agent-control accepts for `8081/8083/8085`
    (parity row A35); no broad `br-*` accept exists.
  - Container-IP anti-spoof and loopback guards render in `raw_prerouting`
    (priority -300, pre-DNAT), never in forward or input.
  - Meters render as `limit rate over N/minute burst B packets`, preserving the
    live `--hashlimit-above` drop side.
  - The forward chain's final unconditional `accept` is a CONFIRMED NON-ISSUE.
    A base-chain `accept` CONTINUES to the next base chain in the same hook, so
    Docker's `ip filter FORWARD` at priority 0 (policy DROP) still runs and
    still enforces per-bridge/per-port policy. Packet-level proof (task-40b:
    an unpublished container port stays dropped while Docker's published-port
    counter increments) is in `.omo/evidence/task-40b-forward-accept.md`.
- **Single tunnel owner.** `wg-quick@client` remains the only lifecycle owner. The
  VPN agent writes `client.conf` atomically (0600, `.viswall-backup` copy) and
  restarts/enables/disables the unit through `nsenter`. It never runs `wg-quick up`
  as a second manager. Startup reconciliation is gated behind the takeover marker
  `/var/lib/viswall-vpn/takeover`, created only at todo 42.
- **Persistence at boot.** `viswall-firewall-persist.service` loads a table-scoped
  dump (`nft list table inet viswall > /etc/nftables.conf`) with
  `Before=network-pre.target` and `Conflicts=nftables.service`, so the filter is in
  place before the network is up. Never dump `nft list ruleset` into that file.
- **`/block` is host-INPUT-only (F2 REMAINING MINOR #2, documented scope
  decision).** The `/block` endpoint (todo-20 carryover) adds timed elements to
  the `blacklist_v4`/`blacklist_v6` sets, which the renderer references at the
  TOP of the input chain — immediately after the conntrack
  established/related accept and before loopback/ICMP/meters/management
  accepts — so a blocked source IP reaches no host INPUT service, including
  previously open ports. The blacklist is deliberately NOT referenced in the
  forward chain: forwarded / docker-published traffic from a blacklisted IP is
  Docker's concern (Docker's own forward chains at priority 0 keep enforcing
  per-bridge/per-port policy). This is a scope decision, not a gap — no
  forward-chain blacklist change.
- **WireGuard and NAT inputs are parsed at the boundary.** Every value that can
  reach `client.conf` (`allowed_ips`, `local_address`, `endpoint`,
  `peer_public_key`, `private_key`) is validated (CIDR/interface/host:port/
  44-char base64, newline, CR and `=` rejected) by `shared/schemas.py` before
  it is stored or rendered, so a config field cannot inject a `PostUp` line.
  NAT `to_source`/`to_destination` use the same strict `address[:port]` parse
  and reject nft statement injection.
- **VPN key material is admin-only.** `VPNClientResponse` carries no
  `config_file`/`config_qr` and `VPNServerResponse` carries no `private_key`;
  the fields exist only on `VPNClientAdminResponse` / `VPNServerAdminResponse`,
  returned by `require_admin` routes. The Python SDK, TypeScript SDK, CLI and
  web-ui mirror that split (plain list/detail shapes, admin create/update and
  config-download shapes), so a non-admin cannot read a client or tunnel key.
- **Apply and rollback keep a last-good firewall.** `apply_ruleset` copies the
  current `/etc/nftables.conf` to `$STATE_DIR/nftables.conf.last-good` before
  the swap, validates the new render with `nft -c -f` before deleting the
  table, and re-applies the last-good file if `nft -f` fails. The agent's direct
  rollback validates the snapshot first and re-applies last-good if a restore
  fails midway, so the host is never left with neither firewall.
- **The restore script's no-op guard runs first.** `restore_firewall.sh` exits
  0 on `$STATE_DIR/COMMIT` or fresh `$STATE_DIR/ALIVE` BEFORE it disables the
  persist unit or deletes the table. A scheduled fire can therefore never
  mutate anything.

---

## 3. Phase plan

| Phase | Name | Primary todos | Gate to leave the phase |
| --- | --- | --- | --- |
| 0 | Repo prep | 2 | branch exists on origin, based on `origin/main` |
| 1 | Module hardening | 6-17 | agents tested, auth enforced, renderer docker-safe |
| 2 | Cold backup | 3 | tar + SHA256 + restore proof recorded |
| 3 | Import | 34-37 | dry-run reviewed, `--apply` with validation mode armed |
| 4 | Parallel validation | 38-43 | netns, parity, pass-through, drills, VPN, gate all green |
| 5 | Cutover | 44 | window under 30 min, COMMIT written, traps stopped |
| 6 | Verification | 45 | t0 and t+24h batteries, reboot rehearsal, day-2 edit |
| 7 | Rollback | 46 | undo chain audited, never executed live post-cutover |
| 8 | Decommission | 48-49 | 14 day soak clean, archive off-host, wg perms 600 |

### Phase 0: Repo prep (done)

Fresh clone `/data/docker/persistent/viswall/viswall-fwdev`, branch
`feat/firewall-production` from `origin/main`
`fcd8089fdbebd0aed5ae1e10cbe74777110366e2` (the merge commit for PR #71). The branch
was pushed and advertised the same SHA at creation time. The retired pre-CD clone
and `/opt/viswall` are out of bounds.

### Phase 1: Module hardening (todos 6-17)

- `services/firewall-service/` becomes a package with `main.py`, `api.py`, `nft.py`,
  `snapshots.py`, `qos.py`, `routing.py`, `heartbeat.py`. Netplan management is not
  here: the node-agent (`services/node-agent/`) owns interfaces and netplan.
  Auth middleware requires `X-Instance-Key` on everything except `/health`,
  compared with `secrets.compare_digest`.
- `services/vpn-service/` becomes a WG client manager package (`wg_client.py`,
  `api.py`, `heartbeat.py`) with the ownership model from section 2.
- Renderer invariants, all regression-tested:
  - `table inet viswall` only, zero occurrences of `flush ruleset`.
  - SSH 22, established/related and WG 51820 accepts always precede user rules.
  - Every meter is port-scoped, and the single-bucket rule holds: imported DB rows
    carrying `limit` are the only source; hardcoded defaults apply only when no
    row exists.
  - Container anti-spoof in `raw_prerouting` (pre-DNAT), never in FORWARD or INPUT;
    loopback guards imported as INPUT rows and rendered in `raw_prerouting`.
  - Blacklist drops at the TOP of the input chain (after conntrack, before every
    accept), so `/block` has precedence over open ports; blacklist is never
    referenced in forward.
  - Broad INPUT accept is `docker0` only. The only `br-*` INPUT accepts are the
    port-scoped agent-control accepts `iifname "docker0"/"br-*" tcp dport
    {8081, 8083, 8085} accept` (parity A35), because the bridge-net gateway
    dispatches via `host.docker.internal`. Bridge forwarding accepts;
    ICMP/ICMPv6 are rate-capped at 5/second (no DHCP rule is rendered).
  - Meters render with `limit rate over N/minute burst B packets` (the `over`
    keyword keeps the drop on the over-limit side).
  - IPv6 accepts scoped with `meta nfproto ipv6` exactly as `rules.v6.live`.
  - No masquerade generated by viswall.
  - Forward chain ends in `accept`; that is safe because a base-chain `accept`
    continues to Docker's priority-0 forward chain (packet-level proof in
    `.omo/evidence/task-40b-forward-accept.md`).
- Security posture, all regression-tested (F2 review, converged):
  - WireGuard fields (`allowed_ips`, `local_address`, `endpoint`,
    `peer_public_key`, `private_key`) are validated at the schema boundary
    (newline/CR/`=` injection rejected); NAT `to_source`/`to_destination` are
    parsed as strict `address[:port]`.
  - Client config (`config_file`/`config_qr`) and server/tunnel `private_key`
    are admin-only (`VPNClientAdminResponse`/`VPNServerAdminResponse`); the
    SDKs, CLI and web-ui mirror the plain/admin response split.
  - `apply_ruleset` saves `$STATE_DIR/nftables.conf.last-good` before the swap
    and re-applies it when `nft -f` fails; direct rollback re-applies last-good
    if a snapshot restore fails midway.
  - `restore_firewall.sh` exits 0 on `COMMIT` or fresh `ALIVE` before any
    destructive step.
- Dead-man-switch harness: the prober is authored in
  `scripts/ssh_watchdog.sh` with `deployments/docker/viswall-ssh-watchdog.service`
  (installed at cutover; not self-installing), implementing section 4.
- `VALIDATION_MODE=1` renders a pass-through table (all policies accept, no
  drop/limit/meter rules, `VW-VALIDATION` log prefix, log rate 10/minute) and
  `/firewall/status` reports `validation_mode: true`. The repo default stays 1 and
  the host `.env` flips to 0 only inside the cutover window. **Posture
  warning (F2 review #9): VALIDATION_MODE=1 renders an ACCEPT-ALL host — every
  INPUT/FORWARD policy is `accept` and nothing is dropped, rate-limited or
  blacklisted. It exists purely to observe log flows without risk; it must
  never be armed on a public host outside the bounded validation window, and
  must never be mistaken for a protecting firewall.**

### Phase 2: Cold backup (done)

`/data/docker/persistent/backup/firewall-20261022-221901/` and
`/data/docker/persistent/backup/firewall-20261022-221901.tar.gz` (147 entries,
SHA256 `c98ac33051de461fd5999cc6654b3f0ae2d3c59f86e94e036f085f3b62bc2dff`).

Contents include `rules.v4.live`, `rules.v6.live`, `nft-ruleset.live`,
`iptables-dir/`, `netplan/`, `wireguard/`, `nftables.conf`, `sysctl.conf`,
`ip-{addr,route,rule,link}.json`, `tc-qdisc.txt`, `wg-show.txt`,
`docker-networks.txt`, `docker-ps-inspect.json`, `viswall-compose-ps.txt`,
`viswall-db.sql.gz` and the Ansible remnants snapshot.

Verification at capture: `iptables-restore --test` rc=0 for v4 and v6,
`gzip -t` rc=0, restore into a scratch database reproduced `instances` count 1
(live 1, restored 1), scratch database dropped afterwards. The borgmatic run at
02:00 the same night picks the backup up.

### Phase 3: Import (todos 34-37)

- `scripts/migrate_legacy_firewall.py` consumes `rules.v4.live` / `rules.v6.live`,
  not `/etc/iptables/rules.v4`. It starts with a divergence report between file and
  live capture.
- Mapping: INPUT accepts → `FirewallRule` rows; hashlimit lines → `limit` field
  (`ssh_limit`, `http_limit`, `https_limit`, `wireguard_limit`); the 5432 drop → a
  drop row; input policy drop stays the agent default, not a row; 63 raw
  container-IP drops (48 v4 + 15 v6) → rows with negated `interface_in`, rendered
  in `raw_prerouting` (pre-DNAT); 12 loopback guards → INPUT rows (hoisted to
  `raw_prerouting` by the renderer); the 17 DOCKER-USER ports → one named rule
  `docker-internal-port-protection`; Docker NAT → skipped with a report; the 48
  duplicate MASQUERADE lines → detected, counted, reported, not imported.
- `scripts/migrate_legacy_interfaces.py` imports netplan (WAN static), the WG client
  (endpoint, allowed IPs, keepalive, local address, peer public key; key material
  stored once in the console model with an audit note), and live interfaces
  (docker0, br-*, client, veth with `type: other`).
- Both scripts are dry-run by default, support `--apply`, `--rollback` and an import
  manifest, and are idempotent by name per instance.
- `--apply` runs only after validation mode is confirmed true (todo 36 step 0).

### Phase 4: Parallel validation (todos 38-43)

1. **Netns rehearsal (38):** `ip netns add vwtest`, docker-like fixture chains,
   renderer output applied inside the namespace. Proves ssh meter, dport scoping,
   anti-spoof, DOCKER-USER equivalence, docker chain survival, and the strip script.
   Nothing runs in the host root namespace.
2. **Parity checklist (39):** line by line, live capture vs generated
   `inet viswall`, each row PASS or DIFF with a reason. Zero unexplained DIFFs. Also
   the acceptance gate for cutover.

   **Parity gate (authoritative, todo 39b):** `docs/firewall-parity-checklist.md`
   is the gate, not this summary. Its converged state is **137 PASS / 4 intentional
   DIFF** (141 rows). The four DIFFs, each with a written reason:
   A05 icmp and A06 icmpv6 (rate-capped 5/second accepts per the todo-7 design),
   A35 agent-control INPUT accepts on `docker0`/`br-*` (8081/8083/8085), and
   A36 the declared+referenced blacklist sets. Any other DIFF, or any un-reasoned
   row, blocks cutover.
3. **Pass-through on the host (40):** watchdog armed first, `VALIDATION_MODE=1`
   table live, full connection matrix before and after (ssh 22, 443, mail
   25/465/587/993/995, dns 53 tcp+udp, rustdesk 21114-21119, wg handshake, one
   internal port from inside accepted and from the public path denied), counter
   baselines diffed. Then disarm, `nft delete table inet viswall`, verify the
   `iptables-save` hash is unchanged.
4. **Drills (41):** watchdog kill test with the main prober stopped, netplan
   add/remove roundtrip, forced-fail netplan auto-revert, full restore rehearsal
   with `--no-restart-docker`.
5. **VPN validation (42):** takeover marker, status before/after stop/start,
   handshake restored, `ping 10.80.0.1` through the tunnel, no-op AllowedIPs edit,
   trap disarmed and COMMIT absent. Stop drill only from a session on the public IP
   and with the prober's `--ignore-wg` flag, otherwise the trap auto-restores.
6. **Gate (43):** evidence pack, second independent WAN SSH session, Hetzner console
   login verified inside the window, rollback runbook printed, this document marked
   READY and reviewed.

### Phase 5: Cutover runbook (todo 44), order is mandatory

Window target: under 30 minutes. Two SSH sessions open (public IP), KVM console
ready, rollback runbook in hand.

1. Confirm the second SSH session and Hetzner console access.
2. Take a **fresh** snapshot with the agent snapshot routine and arm the sliding
   window watchdog plus revert trap. `RESTORE_FLAGS` is the FULL restore for this
   window.
3. Set `VALIDATION_MODE=0` in the host `.env` (documented exception to the
   `/opt/viswall` no-edit rule), run `docker compose up -d firewall-service`,
   confirm `/firewall/status` reports `validation_mode: false`. Apply the real
   ruleset via the console. Confirm the normalized drift reference mtime is newer
   than the apply timestamp. Prove a fresh SSH login before continuing.
4. Probe battery: ssh 22 fresh login, 80/443, 25/465/587/993/995, 53 tcp+udp, wg
   handshake, internal port accepted from inside and dropped from `enp0s31f6`.
5. Surgical iptables strip with the rehearsed `strip_to_docker_baseline.sh` against
   the fresh snapshot of this window, never `iptables -F`/`-X`. Run
   `iptables-restore -w 30 --test` first, then restore. Same for ip6tables. HARD
   GATE: the INPUT parity diff against the viswall table must be 100 percent PASS.
6. Re-run the probe battery including a fresh SSH login.
7. `systemctl disable --now netfilter-persistent` (files stay on disk). Write
   `nft list table inet viswall > /etc/nftables.conf` and enable
   `viswall-firewall-persist.service`.
8. Re-run the probe battery and fresh SSH login.
9. Write `/var/lib/viswall-firewall/COMMIT` and explicitly stop
   `vw-revert.timer` and `vw-revert.service`.
10. Disarm the legacy generator trigger per section 9. On this host there is
    nothing local to disable; the operator pauses the off-host Ansible control
    node and records the re-enable command.
11. Audit-log the cutover.

Any probe failure before step 9: let the trap restore, diagnose, fix, and re-enter
from step 2. Never improvise inside the window.

#### Cutover readiness gate (todo 43) — status 2026-10-23

Technical items **GREEN** (evidence pack: `.omo/evidence/task-43-readiness.md`): netns validation
(todo 38), parity checklist 137 PASS / 4 intentional DIFF (todo 39), watchdog + revert-trap drills
and byte-identical restore rehearsals (todos 40/41), VPN live roundtrip with a tunnel-carrying
proof (todo 42), cold backup SHA256 verified, `iptables-restore --test` green on both the cold
backup and the newest agent snapshot, rollback runbook present, and two distinct `who` entries
including a new connection through the public IP.

**WAN-SSH evidence gate (mandatory):** every firewall-state-changing step above must record a
fresh `ssh` login over the public IP — a NEW connection, timestamped — in the cutover evidence
BEFORE proceeding. The automated prober's checks are loopback-scoped; a policy-routing failure
that kills only WAN tcp/22 would otherwise go unnoticed.

**Container-churn drift (found 2026-10-23 — must be handled in the window):** the legacy raw
anti-spoof rows are keyed on live container IPs. Between the cold capture (2026-10-22 22:21,
63 anti-spoof drops) and the first post-deploy snapshot (2026-10-23 09:41, 65 drops) the
api-gateway container was recreated and two rows appeared (`anti-spoof 172.17.0.7 via docker0`
and `anti-spoof 2001:db8:1::7 via docker0`). The console had been imported from the cold capture,
so the rendered table would have silently dropped those two protections at the strip. They have
been imported (console now holds 109 rows, matching the newest snapshot), but the window MUST
repeat the reconciliation against its own fresh snapshot.

**Who generates them:** the todo-1 investigation found the off-host Ansible generator *dormant*
(last activity 2025-10-26, no local trigger), and a 2026-10-23 correlation is conclusive: **all 46
live container IPv4s across every docker network have a matching raw PREROUTING drop** (two stale
entries remain for removed containers). The set is reconciled to the live container set by the
container runtime on every start/stop, not by Ansible — it will keep drifting with container churn.

**Window requirements:**

1. **Freeze container churn** for the window (no deploys, no `docker compose up/restart` of
   unmodified services) and confirm no `/etc/iptables` or live-rule write occurs for a full
   interval before the snapshot (this also covers any dormant/unidentified automation; record the
   re-enable command if something is paused off-host).
2. Take the fresh snapshot (step 2).
3. `python3 scripts/migrate_legacy_firewall.py --apply --rules-file <snap>/rules.v4
   --rules6-file <snap>/rules.v6` (idempotent name-skip). It must report only container-churn
   deltas; anything else is a stop-and-investigate.
4. After applying the real ruleset, run `python3 scripts/firewall_parity_gate.py --rules-v4
   <snap>/rules.v4 --rules-v6 <snap>/rules.v6 --nft-table <(nft list table inet viswall)`.
   Any DIFF blocks the iptables strip.

**Status: PENDING — OPERATOR ITEMS (do not start the window):**

- [ ] Container churn is frozen for the window and no off-host automation will write the rules
      during it (the todo-1 generator is dormant; record the re-enable command if anything is paused).
- [ ] An independent second SSH session from the operator workstation to the public IP, open for
      the whole window (a host-originated connection proves the path but cannot survive a
      host-level failure).
- [ ] Hetzner KVM/rescue console reachability verified (inside the window).
- [ ] Maintenance window announced/confirmed, target under 30 minutes.
- [ ] Rollback runbook (section 7) visible in the second session.
- [ ] Explicit GO for the cutover.

Mark this section **READY, reviewed** only when all six are checked.

### Phase 6: Verification (todo 45)

Full probe battery at t0 and t+24h, Docker publish spot checks (nextcloud,
rustdesk 21115-21119, vidForge, openspeedtest, mattermost, n8n), mail smoke, DNS
dig, WG handshake. Day-2 operability: add a throwaway accept for an unused port via
the console, see it in `nft list table inet viswall` within 10 s, delete it, see it
gone. Reboot rehearsal in the same week: after boot the table is present and Docker
chains coexist; the persist unit ran before the NIC carrier. After every later CD
deploy, confirm `validation_mode: false`.

### Phase 7: Rollback

See section 7. Audited in todo 46, never executed live after cutover.

### Phase 8: Decommission (todos 48-49)

14 day soak with daily evidence, one mid-soak console edit, one Docker restart
coexistence test with a MASQUERADE re-count against the live baseline, borg coverage
for `/etc/iptables`, `/etc/netplan`, `/etc/wireguard`, `/etc/nftables.conf`. After
soak: archive the backup plus newest snapshots off-host for at least 6 months, move
`rules.v4`/`rules.v6` to `/etc/iptables/backups/` with a README pointing at
`restore_firewall.sh`, harden `client.conf` to 0600, update the docs. Do not delete
the legacy files and do not remove `wg-quick@client`.

---

## 4. Watchdog and revert trap (dead-man switch)

Quoted from `.omo/plans/firewall-migration.md` todo 40 (punctuation normalized to
this document's style; thresholds, unit names and command lines unchanged). The
prober is authored in `scripts/ssh_watchdog.sh`; its systemd unit is
`deployments/docker/viswall-ssh-watchdog.service`. Both exist in the repo and are
installed to the host at cutover (the unit is not self-installing).

> **(a) TRUE SLIDING WINDOW.** The prober loop (every 30 s) first evaluates ALL
> checks in (c) and (d). ONLY if every check passes does it run
> `systemctl stop vw-revert.timer vw-revert.service || true` and then re-arm
> `systemd-run --on-active=15m --unit=vw-revert /usr/local/sbin/restore_firewall.sh $RESTORE_FLAGS`,
> and only while `/var/lib/viswall-firewall/COMMIT` does not exist, VERIFYING each
> re-arm with `systemctl is-active vw-revert.timer` (on unit-name reuse failure log
> "RE-ARM FAILED" and retry next cycle; a silently missing trap is unacceptable). On
> ANY failed check it touches NOTHING, so the armed timer keeps its countdown and
> fires the restore on expiry (the deadline slides ONLY with proof-of-life,
> guaranteeing the trap fires when SSH dies, not merely when the prober dies;
> `RESTORE_FLAGS` from the prober config defaults to `--no-restart-docker` during
> todos 40-43 and to full restore during todo 44).
>
> **(b)** `restore_firewall.sh` exits 0 immediately when COMMIT exists OR ALIVE mtime
> < 120 s (spurious fires are no-ops).
>
> **(c) proof-of-life.** The prober touches ALIVE only when a FRESH SSH login to
> 127.0.0.1:22 succeeds (real `ssh -o BatchMode=yes` with the operator key) AND
> `curl -fsS http://127.0.0.1:8010/health` AND `wg show client latest-handshakes`
> age < 300 s. These are loopback/local-path checks; the WAN SSH path is covered by
> the mandatory second-session WAN login (todo 43, formal evidence gate) and by the
> (d) drift check, because a policy-routing/interface mutation that kills only WAN
> tcp/22 would otherwise leave the prober happy (accepted as layered mitigation,
> not a hole, since the operator's two established sessions survive such a failure
> and can trigger restore manually).
>
> **(d) WAN-path drift check with a STABLE normalized reference.** Raw `nft list`
> output cannot be hashed against the ruleset file because nft normalizes formatting
> AND meter sets/counters churn on every login, including the cutover's own
> mandatory WAN SSH logins. The agent refreshes the normalized reference
> (`nft -j list table inet viswall` with `elem`, `counter`, `bytes`, `packets`,
> `expires`, `handle` stripped, then hashed) after EVERY successful
> `/firewall/apply`, UNCONDITIONALLY, no "trap armed" detection needed (refreshing
> while unarmed is harmless, and misdetecting the trap state as disarmed would skip
> the refresh and self-trigger a restore on a legitimate apply). The prober compares
> each live normalized sample against that reference; meter-element churn from
> logins is thereby excluded by design, and a legitimate console apply updates the
> reference instead of reading as drift. Any drift while the trap is armed = failed
> proof. In todo 40 the first reference is captured right AFTER the pass-through
> apply, and todo 44 step 3 includes a "verify reference mtime is post-apply"
> sub-step. Additionally the runbook instructs the second operator session (todo 43)
> to attempt a WAN SSH login after every apply step.

Resulting state machine (the whole point of the design):

| State at timer expiry | `restore_firewall.sh` behaviour | Operator impact |
| --- | --- | --- |
| `COMMIT` exists | exit 0, no-op | committed cutover is never auto-reverted |
| `ALIVE` mtime < 120 s | exit 0, no-op | spurious fire is harmless; probe re-arms |
| No COMMIT, ALIVE stale | full restore of the previous world | host returns to the legacy firewall |

Operational rules that must not be softened:

- **Disarm before teardown.** Before any `nft delete table inet viswall` outside the
  restore script, stop the prober and `systemctl stop vw-revert.timer vw-revert.service`.
  Deleting the table otherwise reads as drift and self-triggers the trap.
- **COMMIT is reserved for the cutover.** Todo 42 and the drills must never write it.
- **Restore flags.** `--no-restart-docker` for todos 40-43 and all drills; full
  restore (Docker restart included) only in the cutover window.
- **The trap must outlive the prober.** If the prober dies, the timer still fires;
  only proof-of-life slides the deadline.
- **ALIVE is not a heartbeat file.** It is written only after all three local checks
  pass. Do not touch it manually to silence the trap.

`restore_firewall.sh` contract:

1. Exit 0 immediately if `/var/lib/viswall-firewall/COMMIT` exists or ALIVE is
   younger than 120 s. This guard runs BEFORE any destructive operation, so a
   scheduled no-op fire mutates nothing.
2. Disable `viswall-firewall-persist`, delete `table inet viswall` (never a flush).
3. `iptables-restore -w 30` and `ip6tables-restore -w 30` from the snapshot, after
   copying the files back to `/etc/iptables/` and enabling `netfilter-persistent`,
   so boot-time protection is back immediately.
4. Restart Docker (rebuilds its chains) unless `--no-restart-docker` was passed.
5. Restart `wg-quick@client`. Restore netplan files and `netplan apply`.
6. Log every action to `/var/log/viswall-restore.log`. Safe to run repeatedly.

---

## 5. Hetzner KVM and rescue: the last resort

Order of recourse when SSH is gone: (1) the armed trap fires within its window,
(2) the second established SSH session, (3) Hetzner KVM console, (4) rescue system.

**KVM console.** `https://robots.hetzner.com` → Server → `boseman` (`46.4.63.216`) →
**Console** (HTML5 KVM/VNC). Works without network on the host; use it to log in as
root if the filter is wrong but the kernel is alive.

**Rescue system.** Same Robot page → **Rescue** tab → activate the Linux rescue
system, choose the OS and an SSH key. Hetzner shows the root credential in the
Robot panel. Reboot into rescue. No Hetzner credential file exists on the host and
none may be stored there; the operator uses their own Robot account.

**Repair from rescue** (mount the root filesystem first; `/data` lives on it):

```bash
mkdir -p /mnt
mount /dev/<rootdev> /mnt
# restore the legacy snapshot (IPv4 + IPv6)
iptables-restore < /mnt/data/docker/persistent/backup/firewall-20261022-221901/rules.v4.live
ip6tables-restore < /mnt/data/docker/persistent/backup/firewall-20261022-221901/rules.v6.live
# or repair netplan
cp /mnt/data/docker/persistent/backup/firewall-20261022-221901/netplan/01-netcfg.yaml /mnt/etc/netplan/01-netcfg.yaml
```

If the viswall table is the problem, remove it from the mounted root's persisted
file (`/mnt/etc/nftables.conf`) or delete the table after boot with
`nft delete table inet viswall`. Rescue is the only path that works when the WAN
address itself is wrong. It is therefore the documented escape hatch for section 6's
WAN-IP limitation.

---

## 6. Known limitations (accepted, not bugs)

1. **No full-tunnel WireGuard.** The tunnel keeps `AllowedIPs = 10.80.0.0/16`. A
   default route through base0 is explicitly out of scope. Console edits may change
   endpoint, keepalive and allowed IPs, but not the split-tunnel topology without an
   explicit operator decision.
2. **Docker keeps owning NAT.** DNAT, MASQUERADE and the Docker chains are not
   imported and not managed by viswall. The console NAT page exists, but viswall NAT
   is unused in v1 (empty nat chains). Docker restart behavior stays Docker's.
3. **The 48 duplicate MASQUERADE lines are Docker's.** They will reappear after a
   daemon restart or network recreate. Re-counting them in soak is a monitoring
   check, not a regression test. Viswall must never generate masquerade rules.
4. **WAN IP change is operator plus KVM only.** Netplan management can edit the WAN
   entry, but changing `46.4.63.216/32` or the gateway is never automated. It
   requires a session on KVM/rescue and is excluded from every apply path.
5. **IPv6 is deliberately narrower.** `rules.v6.live` opens only 22/80/443/51820.
   The migration preserves that; it does not "upgrade" IPv6 to the IPv4 port set.
6. **Additional accepted risks:** the agents are privileged with host networking
   (mitigated by port-scoped bridge INPUT accepts and instance-key auth); the
   Docker-restart branch of `restore_firewall.sh` is not exercised live until a
   real incident (only `--no-restart-docker` is rehearsed); the Jenkins
   controller at `10.80.2.251:8081` was never contacted and remains an unknown
   for rule generation (section 9).

---

## 7. Rollback runbook

Two forms: the host-native script (preferred) and manual commands (when the script
itself is suspect). Both must restore the previous world exactly and must leave
boot-time protection behind.

### 7.1 Script

```bash
# syntax: restore_firewall.sh [--no-restart-docker] [--dry-run] <snapshot-dir>
# 1. Take a snapshot dir from the agent ($STATE_DIR/snapshots/<ts>) or the cold backup.
/usr/local/sbin/restore_firewall.sh \
  /var/lib/viswall-firewall/snapshots/20261022-230000

# rehearsals only:
/usr/local/sbin/restore_firewall.sh --no-restart-docker --dry-run <snapshot-dir>
```

Sequence inside the script, in this order:

1. Exit 0 if COMMIT exists or ALIVE is younger than 120 s, before any destructive
   step.
2. `systemctl disable --now viswall-firewall-persist` and
   `nft delete table inet viswall`.
3. Copy the snapshot's `rules.v4`/`rules.v6` back to `/etc/iptables/`, enable
   `netfilter-persistent`, then `iptables-restore -w 30` and `ip6tables-restore -w 30`.
4. `systemctl restart docker` unless `--no-restart-docker`.
5. `systemctl restart wg-quick@client`, restore the netplan copy, `netplan apply`.
6. Log to `/var/log/viswall-restore.log`.

### 7.2 Manual (fast path, cold backup)

```bash
cd /data/docker/persistent/backup/firewall-20261022-221901

# If cutover was committed, remove the no-op guard FIRST, or the script-style
# guards will refuse to act. Only do this when a real rollback is intended.
rm -f /var/lib/viswall-firewall/COMMIT
systemctl stop vw-revert.timer vw-revert.service 2>/dev/null || true
systemctl disable --now viswall-firewall-persist 2>/dev/null || true
nft delete table inet viswall 2>/dev/null || true

# Restore both families (the one-liner required by the acceptance criteria):
iptables-restore < rules.v4.live && systemctl restart docker && systemctl restart wg-quick@client
ip6tables-restore -w 30 < rules.v6.live

# Put the files back for boot and re-enable the boot loader:
cp rules.v4.live /etc/iptables/rules.v4
cp rules.v6.live /etc/iptables/rules.v6
chmod 0640 /etc/iptables/rules.v4 /etc/iptables/rules.v6
systemctl enable netfilter-persistent
systemctl start netfilter-persistent

# Netplan (only if interfaces were changed):
cp netplan/01-netcfg.yaml /etc/netplan/01-netcfg.yaml
chmod 0600 /etc/netplan/01-netcfg.yaml
netplan apply
```

Verify after rollback: `iptables-save` matches the snapshot (counters aside),
`nft list table inet viswall` fails with "no such table", a fresh SSH login works,
443 and 25/53 respond, and `wg show client` shows a fresh handshake. If SSH is
still dead, go to section 5 (KVM, then rescue).

**Do not** run `iptables -F`, `iptables -X` or `nft flush ruleset`. Those destroy
Docker's chains and are exactly the failure the trap exists to prevent.

---

## 8. Test-by-following clause

This document is not a suggestion. During todos 38-48 the executor follows it
verbatim and treats every command, threshold and ordering constraint as a test
step:

- Execute the steps in the order written. Do not reorder "for convenience".
- Where reality diverges (a command renamed, a flag missing, an output shape
  different, an extra guardrail needed, a timeout wrong), **patch this document in
  the same session** with a commit named `docs(firewall): correct step <X>`, and
  record the divergence and its evidence in `.omo/evidence/`.
- Evidence beats the document; the document beats memory. If an evidence file
  contradicts a number here, the evidence is right and the doc gets corrected.
- No step may be silently skipped. A step that cannot be executed as written is a
  divergence and must be documented, not omitted.
- Todo 47 is the final reconciliation: diff this document against the executed
  evidence and commit the corrections. After that, a fresh operator must be able to
  re-run the migration or the rollback from this file alone.
- Sections 1, 4, 5, 6 and 7 are the safety-critical ones. Changes there need
  explicit operator sign-off in the evidence file.

---

## 9. Ansible generator verdict (task-1 evidence)

**Verdict: there is no active generator on the host.** `/etc/iptables/rules.v4` and
`rules.v6` are a hand-managed snapshot: an Ansible-era body from 2025-10-25/26 plus
a manual 2026-09-01 DOCKER-USER insertion, loaded at boot by
`netfilter-persistent.service`. `netfilter-persistent` is a **loader**, not a
generator (`start` reads the files; only `save` writes them).

Confirmed history:

- `/etc/iptables/rules.v6:1` says `# Generated by Ansible - DO NOT EDIT MANUALLY`,
  generated `2025-10-25T17:19:42Z` by an **off-host Ansible 2.19.3** control node as
  part of a "Docker Security Integration" run. The on-host Ansible is 2.16.3 and no
  playbook exists there.
- No cron job, systemd timer, unit, CI runner, `rc.local`, UFW, nftables service,
  container or repo playbook writes these files. UFW is disabled; `nftables.service`
  is disabled and inactive; `/etc/nftables.conf` is the Hetzner stub.
- `deployments/ansible/` in the repo (and in both clones) is example-only and
  contains no iptables tasks.
- The only Ansible-managed artifacts still present are the **nginx-backup
  remnants**: `/opt/nginx-backup.sh`, `/opt/nginx-backup-cleanup.sh`,
  `/opt/nginx-backup-verify.sh`, `/opt/nginx-restore.sh`,
  `/etc/logrotate.d/nginx-backup`, `/etc/logrotate.d/redis_backup`, and the root
  crontab entries marked `#Ansible: nginx backup`. None touch the firewall.
- The 2026-09-01 live-file mtime comes from the manual
  `/root/security-fix-backup/rollback.sh`, which is manual-only and dormant.
- One unknown remains: the Jenkins controller at `10.80.2.251:8081` was not
  contacted. Local agent workspaces show only `smoke-comfyui` and `vidforge-release`,
  no firewall job.

Consequence for the cutover: **there is nothing local to disable at todo 44 step 10.**
The operator action is to pause the off-host Ansible control node operationally and
record its re-enable command. `restore_firewall.sh` re-enables
`netfilter-persistent`, so the legacy boot path returns with the rollback. Keep
`/root/security-fix-backup/` and the Ansible-era headers; they are provenance.

Re-check commands (read-only, run before the cutover gate):

```bash
grep -rl "Generated by Ansible" /etc /opt /srv /home 2>/dev/null
grep -rl "FIREWALL-DROP" /etc /opt /srv /home 2>/dev/null
cat /var/spool/cron/crontabs/root
grep -rn "iptables\|ip6tables\|nft \|netfilter" \
  /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly \
  /etc/cron.monthly /etc/crontab /var/spool/cron/crontabs 2>/dev/null
systemctl list-timers --all --no-pager
find /etc/systemd/system -maxdepth 1 -type f -name '*.service' -printf '%f\n'
grep -rln "iptables\|netfilter\|ip6tables\|ansible\|nft " /etc/systemd/system 2>/dev/null
dpkg -l | grep -E '^ii +ansible'
systemctl is-enabled nftables ufw netfilter-persistent
grep -n ENABLED /etc/ufw/ufw.conf
stat -c '%n %s %y' /etc/iptables/rules.v4 /etc/iptables/rules.v6
```

Expected: the only `Generated by Ansible` hits are the rules files and the nginx
scripts/logrotate configs; no firewall cron or timer; `netfilter-persistent`
enabled; `nftables` disabled; no iptables output from the systemd/cron greps.
If any of that changes, stop and re-run the todo-1 analysis before touching the
host.

---

## 10. Instance-1 baseline (task-5 + task-31b evidence)

Read-only snapshot of the console, 2026-10-22 ~20:19 UTC. Exactly one instance row:

```
 id | name  | hostname  |         api_endpoint         | status |          capabilities           |         config
----+-------+-----------+------------------------------+--------+---------------------------------+-------------------------
  1 | Local | localhost | http://localhost:8010/api/v1 | active | ["mail","firewall","vpn","dns"] | {"agent_endpoints": {"dns": "http://dns-service:8082"}}
```

- `capabilities` already contains `firewall` and `vpn`. No capability update is
  needed for this migration.
- At the capture `config.agent_endpoints` had **only** `dns`. The pre-cutover
  update (`scripts/update_instance_1.py`, todo 26/36) writes
  `"firewall": "http://host.docker.internal:8081"`,
  `"vpn": "http://host.docker.internal:8083"` and
  `"node": "http://host.docker.internal:8085"` (node-agent), leaving `dns`
  unchanged and preserving every other config key (especially `version`, which
  the heartbeat response reads). `host.docker.internal` is required because the
  gateway runs in a bridge network, where `127.0.0.1` is the gateway's own
  loopback, not the host where the host-net agents bind. Task-33 evidence still
  showed the dns-only config because the deploy was blocked; the endpoint write
  is a pre-cutover action, not an executed post-cutover fact.
- Heartbeat route: `POST /api/v1/instances/{id}/heartbeat`, implemented in
  `services/api-gateway/routers/instances.py`. Auth is on the **request body**
  `api_key` field, not the `X-Instance-Key` header.
- Real key: HTTP 200, body `{"status":"ok","config_version":1}`, `last_seen`
  advanced. Wrong key: HTTP 401, `{"detail":"Invalid instance or API key"}`, and
  `last_seen` did not move. The env key matches the DB row for id 1.
- Consequence: todo 12's heartbeat loop is safe to implement as a body-key POST to
  `{GATEWAY_URL}/api/v1/instances/1/heartbeat`. Todo 19 does not need to create the
  route. The key value itself is never reproduced in this document.

---

## Appendix A: evidence index

| Evidence | Covers |
| --- | --- |
| `.omo/evidence/task-1-firewall-migration.md` | generator hunt, loaders vs generators, live/file divergence |
| `.omo/evidence/task-2-firewall-migration.md` | clone, branch base SHA, push proof |
| `.omo/evidence/task-3-firewall-migration.md` | cold backup, hashes, restore proof, rescue notes |
| `.omo/evidence/task-4-firewall-migration.md` | this document: creation, secret scan, commit and push proof |
| `.omo/evidence/task-5-firewall-migration.md` | instance row, heartbeat 200/401 proof |

## Appendix B: cutover acceptance checklist (anchor for todo 39)

The authoritative gate is `docs/firewall-parity-checklist.md` (todo 39b): 137 PASS /
4 intentional DIFF (A05/A06 icmp rate-capped accepts, A35 agent-control port
accepts, A36 blacklist sets) out of 141 rows. Every row in that checklist must
resolve to PASS, with a reason string for each intentional DIFF:

- [ ] 22/tcp accept plus `ssh_limit` 10/min burst 5, before any user rule
- [ ] 25/tcp, 110/tcp, 143/tcp, 993/tcp, 995/tcp accepts
- [ ] 53 tcp and udp accepts
- [ ] 80/tcp and 443/tcp accepts plus `http_limit` / `https_limit` 100/min burst 5
- [ ] 51820/udp accept plus `wireguard_limit` 20/min burst 5
- [ ] 21114-21119 tcp, 21116 udp
- [ ] 5432/tcp drop
- [ ] FIREWALL-DROP log with 5/min limit
- [ ] docker0 INPUT accept preserved (broad bridge accept is docker0 only;
      the sole `br-*` accepts are the port-scoped 8081/8083/8085 agent accepts)
- [ ] blacklist drops at the TOP of the input chain, before every accept
- [ ] all 63 container-IP anti-spoof rules (48 v4 + 15 v6) present in `raw_prerouting`
- [ ] all 12 loopback guards present (INPUT rows, rendered in `raw_prerouting`)
- [ ] the 17 DOCKER-USER ports present in the viswall forward rule
- [ ] forward chain's final `accept` continues to Docker's priority-0 chain
- [ ] IPv6 column: 22/80/443/51820 only, same limits
- [ ] Docker chains survive: `DOCKER`, `DOCKER-USER`, `DOCKER-FORWARD`,
      `DOCKER-ISOLATION-*` intact after every apply
- [ ] zero `flush ruleset`, zero viswall masquerade rules
- [ ] `/etc/nftables.conf` contains only `table inet viswall`

## Appendix C: decision log

| Decision | Rationale | Source |
| --- | --- | --- |
| Own table, never flush | Docker owns `ip`/`ip6` tables; a flush kills all hosted workloads | plan scope, task-3 diagnosis |
| Live capture is the import source | persisted files are a stale 8,769 B snapshot vs 23,579 B live | task-1, task-3 |
| Docker NAT not imported | avoids double masquerade and duplicate regeneration | plan todos 34, 48 |
| Trap keyed on proof-of-life, not liveness | prober death must not be enough to keep a broken host | plan todo 40 |
| Fresh snapshot inside the cutover window | container lifecycle changes NAT/DNAT | task-3 note |
| WG single owner stays `wg-quick@client` | avoids dual-manager races | plan todo 15 |
