"""Live DNS verification for a mail domain's expected records."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Awaitable, Callable, List, Optional, Tuple

import dns.asyncresolver
import dns.exception
import dns.resolver
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import MailDomain
from shared.schemas import MailDnsCheckItem, MailDnsCheckResponse, MailDnsCheckStatus

logger = logging.getLogger(__name__)

QUERY_LIFETIME = 5.0
OVERALL_TIMEOUT = 10.0

_ABSENT = (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer)


async def _resolve(qname: str, rdtype: str):
    """Single DNS lookup with a hard per-query lifetime budget."""
    return await dns.asyncresolver.resolve(qname, rdtype, lifetime=QUERY_LIFETIME)


def _normalize(value: str) -> str:
    """Normalize a DNS value for comparison: strip surrounding double quotes
    and trailing dots, collapse internal whitespace runs, lowercase."""
    v = value.strip()
    if len(v) >= 2 and v.startswith('"') and v.endswith('"'):
        v = v[1:-1]
    v = v.rstrip(".")
    return " ".join(v.split()).lower()


def _strip_all_whitespace(value: str) -> str:
    return "".join(value.split())


async def _txt_strings(qname: str) -> List[str]:
    """Joined strings of every TXT record at qname (multi-string rdata chunks
    are concatenated per RFC 7208 style). Raises NXDOMAIN/NoAnswer when the
    name or record type does not exist."""
    answer = await _resolve(qname, "TXT")
    return [
        "".join(
            chunk.decode() if isinstance(chunk, bytes) else str(chunk)
            for chunk in rdata.strings
        )
        for rdata in answer
    ]


def _item(
    key: str,
    rtype: str,
    name: str,
    expected_value: Optional[str],
    status: MailDnsCheckStatus,
    found_values: Optional[List[str]] = None,
    detail: Optional[str] = None,
) -> MailDnsCheckItem:
    return MailDnsCheckItem(
        key=key,
        type=rtype,
        name=name,
        expected_value=expected_value,
        found_values=found_values or [],
        status=status,
        detail=detail,
    )


async def _check_mx(domain: MailDomain) -> MailDnsCheckItem:
    domain_name = domain.domain
    expected = f"10 mail.{domain_name}."
    status: MailDnsCheckStatus = "missing"
    found_values: List[str] = []
    detail: Optional[str] = None

    async def _mx_query() -> None:
        nonlocal status, detail, found_values
        try:
            answer = await _resolve(domain_name, "MX")
        except dns.exception.Timeout:
            status = "error"
            detail = "DNS query timed out"
        except _ABSENT:
            status = "missing"
        except Exception as e:  # unexpected resolver failure
            status = "error"
            detail = str(e) or type(e).__name__
        else:
            records = list(answer)
            found_values = [f"{r.preference} {r.exchange}" for r in records]
            priorities = ", ".join(str(r.preference) for r in records)
            ok = len(records) == 1 and _normalize(str(records[0].exchange)) == _normalize(
                f"mail.{domain_name}."
            )
            status = "correct" if ok else "incorrect"
            detail = f"found priority {priorities}"

    async def _host_probe(rdtype: str) -> bool:
        try:
            await _resolve(f"mail.{domain_name}", rdtype)
            return True
        except Exception:
            return False

    a_ok, aaaa_ok, _ = await asyncio.gather(
        _host_probe("A"), _host_probe("AAAA"), _mx_query()
    )
    host_note = (
        "mail host resolves" if (a_ok or aaaa_ok) else "mail host does not resolve"
    )
    detail_parts = [p for p in (detail, host_note) if p]
    return _item(
        "mx", "MX", domain_name, expected, status, found_values, "; ".join(detail_parts)
    )


async def _check_spf(domain: MailDomain) -> MailDnsCheckItem:
    domain_name = domain.domain
    expected = f"v=spf1 mx a:mail.{domain_name} ~all"
    try:
        values = await _txt_strings(domain_name)
    except dns.exception.Timeout:
        return _item("spf", "TXT", domain_name, expected, "error", detail="DNS query timed out")
    except _ABSENT:
        return _item("spf", "TXT", domain_name, expected, "missing")
    except Exception as e:
        return _item("spf", "TXT", domain_name, expected, "error", detail=str(e) or type(e).__name__)

    spf_values = [v for v in values if _normalize(v).startswith("v=spf1")]
    if not spf_values:
        return _item("spf", "TXT", domain_name, expected, "missing")
    ok = any(_normalize(v) == _normalize(expected) for v in spf_values)
    return _item(
        "spf", "TXT", domain_name, expected,
        "correct" if ok else "incorrect", spf_values,
    )


async def _check_dkim(domain: MailDomain) -> MailDnsCheckItem:
    domain_name = domain.domain
    qname = f"{domain.dkim_selector}._domainkey.{domain_name}"
    expected = f"v=DKIM1; k=rsa; p={domain.dkim_public_key}"
    try:
        values = await _txt_strings(qname)
    except dns.exception.Timeout:
        return _item("dkim", "TXT", qname, expected, "error", detail="DNS query timed out")
    except _ABSENT:
        return _item("dkim", "TXT", qname, expected, "missing")
    except Exception as e:
        return _item("dkim", "TXT", qname, expected, "error", detail=str(e) or type(e).__name__)

    v_ok = False
    p_found: Optional[str] = None
    for value in values:
        for tag in value.split(";"):
            tag = tag.strip()
            tag_name, _, tag_value = tag.partition("=")
            tag_name = tag_name.strip().lower()
            if tag_name == "v" and _strip_all_whitespace(tag_value).lower() == "dkim1":
                v_ok = True
            elif tag_name == "p" and p_found is None:
                p_found = tag_value

    ok = (
        v_ok
        and p_found is not None
        and _strip_all_whitespace(p_found)
        == _strip_all_whitespace(domain.dkim_public_key or "")
    )
    return _item(
        "dkim", "TXT", qname, expected, "correct" if ok else "incorrect", values
    )


async def _check_dmarc(domain: MailDomain) -> MailDnsCheckItem:
    domain_name = domain.domain
    qname = f"_dmarc.{domain_name}"
    expected = f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain_name}"
    try:
        values = await _txt_strings(qname)
    except dns.exception.Timeout:
        return _item("dmarc", "TXT", qname, expected, "error", detail="DNS query timed out")
    except _ABSENT:
        return _item("dmarc", "TXT", qname, expected, "missing")
    except Exception as e:
        return _item("dmarc", "TXT", qname, expected, "error", detail=str(e) or type(e).__name__)

    ok = any(_normalize(v) == _normalize(expected) for v in values)
    return _item(
        "dmarc", "TXT", qname, expected, "correct" if ok else "incorrect", values
    )


async def run_dns_check(db: AsyncSession, domain: MailDomain) -> MailDnsCheckResponse:
    """Run all applicable DNS lookups for a mail domain concurrently and
    compare what DNS returns against the records the appliance expects.

    Per-record lookups get a 5s lifetime; the whole batch is capped at 10s —
    records that have not finished by then come back as status="error"."""
    check_fns: dict[str, Callable[[MailDomain], Awaitable[MailDnsCheckItem]]] = {
        "mx": _check_mx,
        "spf": _check_spf,
        "dkim": _check_dkim,
        "dmarc": _check_dmarc,
    }

    specs: List[Tuple[str, str, str, Optional[str]]] = [
        ("mx", "MX", domain.domain, f"10 mail.{domain.domain}.")
    ]
    if domain.spf_enabled:
        specs.append(
            ("spf", "TXT", domain.domain, f"v=spf1 mx a:mail.{domain.domain} ~all")
        )
    if domain.dkim_enabled and domain.dkim_public_key:
        specs.append(
            (
                "dkim",
                "TXT",
                f"{domain.dkim_selector}._domainkey.{domain.domain}",
                f"v=DKIM1; k=rsa; p={domain.dkim_public_key}",
            )
        )
    if domain.dmarc_enabled:
        specs.append(
            (
                "dmarc",
                "TXT",
                f"_dmarc.{domain.domain}",
                f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain.domain}",
            )
        )

    results: dict[str, MailDnsCheckItem] = {}

    async def _run(key: str, check: Awaitable[MailDnsCheckItem]) -> None:
        results[key] = await check

    runners = [_run(key, check_fns[key](domain)) for key, _, _, _ in specs]
    try:
        await asyncio.wait_for(asyncio.gather(*runners), timeout=OVERALL_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning(
            "DNS check for %s hit the overall timeout; unfinished records marked as errors",
            domain.domain,
        )

    items: List[MailDnsCheckItem] = []
    for key, rtype, name, expected in specs:
        item = results.get(key)
        if item is None:
            item = _item(
                key, rtype, name, expected, "error", detail="DNS query timed out"
            )
        items.append(item)

    return MailDnsCheckResponse(
        checked_at=datetime.now(timezone.utc), results=items
    )
