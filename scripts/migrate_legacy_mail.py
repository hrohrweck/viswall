#!/usr/bin/env python3
"""
Migrate legacy Exim/Courier MariaDB `exim` -> Viswall Postgres (faithful model).

Decisions: email-as-login; aliases/catch-alls migrated into mail_aliases.

Legacy: Mailusers.Benutzername = mailbox login ("lp.domain", "lp@domain", or bare);
Passwort CLEARTEXT. Aliases.Email -> Forwarder (mailbox login | external | empty),
Email may be "*@domain" (catch-all). LocalMailDomains/AdditionalMailDomains = domains.

Target: mail_domains(domain), mail_users(username,domain_id,password_hash),
mail_aliases(source,domain_id,destination)  [source '*' = catch-all; one row per target].

Mailbox -> username@domain:
  * resolvable login -> username=lp, domain=dom
  * bare login -> canonical from an alias (Forwarder==login, Email has @); prefer localpart==login;
    else --default-domain; else UNRESOLVED (reported, skipped on commit)
Alias -> mail_aliases: destination = Forwarder (external as-is; mailbox login -> its canonical
  email). Self rows (source==mailbox and dest==its own address) are skipped (mailbox delivers;
  the exim alias_copy router adds extra recipients).

DRY-RUN by default. --commit writes domains + resolvable/derived mailboxes + aliases.
Requires: pymysql, psycopg2-binary, bcrypt.
"""
import os, argparse


def hash_pw(pw: str) -> str:
    import bcrypt
    return bcrypt.hashpw(pw.encode("utf-8")[:72], bcrypt.gensalt()).decode("ascii")


def quota_to_bytes(q):
    if not q:
        return None
    s = str(q).strip().upper().rstrip("S")
    if not s:
        return None
    mult = 1
    if s and s[-1] in "KMG":
        mult = {"K": 1024, "M": 1024**2, "G": 1024**3}[s[-1]]; s = s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--quotas-only", action="store_true",
                    help="Backfill quota_bytes from legacy Mailusers only (no domains/mailboxes/aliases). "
                         "Requires a throwaway MariaDB container loaded from the verified dump.")
    ap.add_argument("--instance-id", type=int, default=int(os.getenv("INSTANCE_ID", "0")) or None)
    ap.add_argument("--default-domain", default=os.getenv("DEFAULT_DOMAIN", ""))
    ap.add_argument("--emit-map", help="write login<TAB>domain<TAB>username TSV and exit")
    ap.add_argument("--overrides", default=os.getenv("OVERRIDES", ""), help="TSV: login<TAB>username<TAB>domain to force identities")
    args = ap.parse_args()

    import pymysql, psycopg2
    my = pymysql.connect(host=os.getenv("MYSQL_HOST", "127.0.0.1"), port=int(os.getenv("MYSQL_PORT", "3306")),
                         user=os.getenv("MYSQL_USER", "viswall"), password=os.getenv("MYSQL_PASSWORD", ""),
                         database=os.getenv("MYSQL_DB", "exim"), charset="latin1")
    pg = psycopg2.connect(host=os.getenv("PG_HOST", "127.0.0.1"), port=int(os.getenv("PG_PORT", "5432")),
                         user=os.getenv("PG_USER", "viswall"), password=os.getenv("PG_PASSWORD", ""),
                         dbname=os.getenv("PG_DB", "viswall"))
    myc = my.cursor(pymysql.cursors.DictCursor); pgc = pg.cursor()

    myc.execute("SELECT Domain FROM LocalMailDomains WHERE active=1")
    doms = {(r["Domain"] or "").strip().lower() for r in myc.fetchall() if r["Domain"]}
    myc.execute("SELECT Domain FROM AdditionalMailDomains WHERE active=1")
    doms |= {(r["Domain"] or "").strip().lower() for r in myc.fetchall() if r["Domain"]}
    doms_by_len = sorted(doms, key=len, reverse=True)

    def parse_login(bn):
        bn = (bn or "").strip().lower()
        if not bn:
            return None, None
        if "@" in bn:
            lp, _, d = bn.partition("@"); return lp, d
        for d in doms_by_len:
            if bn.endswith("." + d):
                return bn[:-(len(d) + 1)], d
        return None, None

    myc.execute("SELECT Benutzername, Passwort, quota, active FROM Mailusers")
    mailboxes = []
    for r in myc.fetchall():
        lp, d = parse_login(r["Benutzername"])
        mailboxes.append({"login": (r["Benutzername"] or "").strip().lower(), "pw": r["Passwort"] or "",
                          "active": bool(r["active"]), "quota": r["quota"], "lp": lp, "dom": d})

    myc.execute("SELECT Email, Forwarder FROM Aliases WHERE active=1")
    araw = [((r["Email"] or "").strip().lower(), (r["Forwarder"] or "").strip().lower()) for r in myc.fetchall()]

    login_canon = {m["login"]: (m["lp"], m["dom"]) for m in mailboxes if m["dom"]}
    for m in mailboxes:
        if m["dom"]:
            continue
        cands = [e for (e, f) in araw if f == m["login"] and "@" in e and not e.startswith("*@")]
        chosen = None
        for e in cands:
            lp, _, d = e.partition("@")
            if lp == m["login"] and d in doms:
                chosen = (lp, d); break
        if not chosen:
            for e in cands:
                lp, _, d = e.partition("@")
                if d in doms:
                    chosen = (lp, d); break
        if not chosen and args.default_domain:
            chosen = (m["login"], args.default_domain)
        if chosen:
            login_canon[m["login"]] = chosen

    # Manual identity overrides (login -> username, domain) take precedence over guesses
    if args.overrides and os.path.exists(args.overrides):
        for line in open(args.overrides):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            login = parts[0].strip().lower()
            if len(parts) >= 2 and parts[1].strip().lower() in ("drop", "-"):
                login_canon.pop(login, None)  # exclude this mailbox from migration
                continue
            if len(parts) >= 3:
                login_canon[login] = (parts[1].strip().lower(), parts[2].strip().lower())

    if args.quotas_only:
        parsed = []
        skipped = []
        ambiguous = []
        for m in mailboxes:
            qb = quota_to_bytes(m["quota"])
            if qb is None:
                if m["quota"]:
                    skipped.append((m["login"], m["quota"], "no quota parse"))
                continue
            login = m["login"]
            lp = d = None
            if "@" in login:
                lp, _, d = login.partition("@")
            else:
                for dd in doms_by_len:
                    if login.endswith("." + dd):
                        lp, d = login[:-(len(dd) + 1)], dd; break
                if lp is None:
                    lp = login
            if lp is None:
                skipped.append((login, m["quota"], "unparseable login"))
                continue
            if d:
                pgc.execute("SELECT u.id FROM mail_users u JOIN mail_domains d ON u.domain_id=d.id "
                            "WHERE u.username=%s AND d.domain=%s", (lp, d))
                hits = pgc.fetchall()
                if len(hits) == 1:
                    parsed.append((hits[0][0], lp, d, qb))
                elif len(hits) == 0:
                    skipped.append((login, m["quota"], f"no match {lp}@{d}"))
                else:
                    ambiguous.append((login, m["quota"], f"{len(hits)} rows for {lp}@{d}"))
            else:
                pgc.execute("SELECT u.id, dom.domain FROM mail_users u JOIN mail_domains dom ON u.domain_id=dom.id "
                            "WHERE u.username=%s", (lp,))
                hits = pgc.fetchall()
                if len(hits) == 1:
                    parsed.append((hits[0][0], lp, hits[0][1], qb))
                elif len(hits) == 0 and args.default_domain:
                    pgc.execute("SELECT u.id FROM mail_users u JOIN mail_domains d ON u.domain_id=d.id "
                                "WHERE u.username=%s AND d.domain=%s", (lp, args.default_domain))
                    hits2 = pgc.fetchall()
                    if len(hits2) == 1:
                        parsed.append((hits2[0][0], lp, args.default_domain, qb))
                    elif len(hits2) == 0:
                        skipped.append((login, m["quota"], f"no match {lp}@{args.default_domain}"))
                    else:
                        ambiguous.append((login, m["quota"], f"{len(hits2)} rows for {lp}@{args.default_domain}"))
                elif len(hits) == 0:
                    skipped.append((login, m["quota"], "bare login, no match, no --default-domain"))
                else:
                    ambiguous.append((login, m["quota"], f"bare login matches {len(hits)} domains"))
        print(f"[quotas-only] legacy mailboxes: {len(mailboxes)}  matched: {len(parsed)}  "
              f"skipped: {len(skipped)}  ambiguous: {len(ambiguous)}")
        if skipped:
            print("-- skipped --")
            for login, q, reason in skipped[:30]:
                print(f"   {login:42s} quota={q!r:12s} ({reason})")
        if ambiguous:
            print("-- ambiguous --")
            for login, q, reason in ambiguous[:10]:
                print(f"   {login:42s} quota={q!r:12s} ({reason})")
        if not parsed:
            print("[quotas-only] nothing to update; exiting without commit.")
            return
        updated = 0
        try:
            for uid, lp, d, qb in parsed:
                pgc.execute("UPDATE mail_users SET quota_bytes=%s WHERE id=%s", (qb, uid))
                updated += pgc.rowcount
            if args.commit:
                pg.commit()
                print(f"\n[quotas-only][commit] updated {updated} rows.")
            else:
                pg.rollback()
                print(f"\n[quotas-only] DRY-RUN: would update {updated} rows. Use --commit to write.")
        except Exception as e:
            pg.rollback()
            print(f"\n[quotas-only] ERROR: {e} — ROLLED BACK, no rows changed.")
            raise
        return

    def canon(login):
        c = login_canon.get(login)
        return f"{c[0]}@{c[1]}" if c else None

    resolved = [m for m in mailboxes if m["login"] in login_canon]
    unresolved = [m for m in mailboxes if m["login"] not in login_canon]

    if args.emit_map:
        n = 0
        with open(args.emit_map, "w") as fh:
            for m in mailboxes:
                c = login_canon.get(m["login"])
                if c:
                    fh.write(m["login"] + "\t" + c[1] + "\t" + c[0] + "\n"); n += 1
        print("wrote maildir map:", args.emit_map, "entries=", n, "unmapped=", len(unresolved))
        return

    alias_rows, unresolved_fwd, foreign_dom = [], [], []
    for e, f in araw:
        if e.startswith("*@"):
            dom = e[2:]; src = "*"
        elif "@" in e:
            src, _, dom = e.partition("@")
        else:
            continue
        if dom not in doms:
            foreign_dom.append((e, f)); continue
        if not f:
            continue
        dest = f if "@" in f else canon(f)
        if not dest:
            unresolved_fwd.append((e, f)); continue
        if dest == f"{src}@{dom}":
            continue
        alias_rows.append((dom, src, dest))

    print("==================== FAITHFUL MIGRATION PREVIEW ====================")
    print(f"domains:                    {len(doms)}")
    print(f"mailboxes:                  {len(mailboxes)} (resolved={len(resolved)}, UNRESOLVED bare={len(unresolved)})")
    print(f"mail_aliases rows to write: {len(alias_rows)} (catch-all={sum(1 for d,s,x in alias_rows if s=='*')})")
    print(f"forwarders unresolved:      {len(unresolved_fwd)}   alias for foreign domain: {len(foreign_dom)}")
    print("-- UNRESOLVED bare mailboxes (no canonical address; need --default-domain or manual) --")
    for m in unresolved:
        print(f"   {m['login']}")
    print("-- sample resolved mailboxes --")
    for m in resolved[:15]:
        print(f"   {m['login']:42s} -> {canon(m['login'])}")
    print("-- sample alias rows --")
    for d, s, x in alias_rows[:20]:
        print(f"   {s}@{d} -> {x}")
    if unresolved_fwd:
        print("-- forwarders that could not be resolved to a mailbox/email --")
        for e, f in unresolved_fwd[:20]:
            print(f"   {e} -> {f}")

    if args.commit:
        inst = None
        if args.instance_id:
            pgc.execute("SELECT 1 FROM instances WHERE id=%s", (args.instance_id,))
            inst = args.instance_id if pgc.fetchone() else None
        dom_id = {}
        def ensure_dom(d):
            if d in dom_id:
                return dom_id[d]
            pgc.execute("SELECT id FROM mail_domains WHERE domain=%s", (d,))
            row = pgc.fetchone()
            if row:
                dom_id[d] = row[0]
            else:
                pgc.execute("INSERT INTO mail_domains (instance_id, domain, enabled) VALUES (%s,%s,TRUE) RETURNING id", (inst, d))
                dom_id[d] = pgc.fetchone()[0]
            return dom_id[d]
        for d in sorted(doms):
            ensure_dom(d)
        mu = 0
        for m in resolved:
            lp, d = login_canon[m["login"]]; did = ensure_dom(d)
            pgc.execute("SELECT id FROM mail_users WHERE domain_id=%s AND username=%s", (did, lp))
            if pgc.fetchone():
                continue
            pgc.execute("INSERT INTO mail_users (domain_id, username, password_hash, enabled) VALUES (%s,%s,%s,%s)",
                        (did, lp, hash_pw(m["pw"]) if m["pw"] else "", m["active"]))  # quota omitted (int4 range); set later
            mu += 1
        al = 0
        for d, s, x in alias_rows:
            did = ensure_dom(d)
            pgc.execute("SELECT id FROM mail_aliases WHERE domain_id=%s AND source=%s AND destination=%s", (did, s, x))
            if pgc.fetchone():
                continue
            pgc.execute("INSERT INTO mail_aliases (domain_id, source, destination, enabled) VALUES (%s,%s,%s,TRUE)", (did, s, x))
            al += 1
        pg.commit()
        print(f"\n[commit] domains={len(dom_id)} mailboxes+={mu} aliases+={al}  (unresolved bare NOT written: {len(unresolved)})")
    else:
        print("\nmode: DRY-RUN (no writes). Use --commit to write.")


if __name__ == "__main__":
    main()
