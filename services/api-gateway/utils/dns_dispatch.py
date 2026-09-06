"""Compose desired DNS state from the database and push it to the dns agent.

One instance runs exactly one named process, so the applied payload merges
every enabled DNSServer row of the instance: zones and TSIG keys are unioned
and server-level options (recursion, ACLs, listen addresses) come from the
primary (lowest-id) server. Deleting the last server applies an empty zone
list with safe options (recursion off), which stops named from serving
stale zones.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import AsyncSessionLocal
from shared.models import DNSRecord, DNSServer, DNSTSIGKey, DNSZone
from utils.agent_client import AgentClientError, agent_request

logger = logging.getLogger(__name__)

DNS_AGENT_SERVICE = "dns"

# Options used when no enabled DNSServer row remains on the instance.
_EMPTY_STATE_OPTIONS: Dict[str, Any] = {
    "server_id": 0,
    "name": "none",
    "listening_addresses": ["0.0.0.0", "::"],
    "port": 53,
    "is_recursive": False,
    "is_authoritative": True,
    "forwarders": [],
    "allow_query": ["0.0.0.0/0", "::/0"],
    "allow_transfer": ["127.0.0.1", "::1"],
    "also_notify": [],
    "tsig_keys": [],
    "zones": [],
}


def _record_payload(record: DNSRecord) -> Dict[str, Any]:
    return {
        "name": record.name,
        "record_type": record.record_type,
        "content": record.content,
        "ttl": record.ttl,
        "priority": record.priority,
        "weight": record.weight,
        "port": record.port,
    }


def _zone_payload(zone: DNSZone) -> Dict[str, Any]:
    return {
        "id": zone.id,
        "name": zone.name,
        "zone_type": zone.zone_type,
        "enabled": zone.enabled,
        "is_reverse": zone.is_reverse,
        "serial": zone.serial,
        "refresh": zone.refresh,
        "retry": zone.retry,
        "expire": zone.expire,
        "minimum_ttl": zone.minimum_ttl,
        "master_server_address": zone.master_server_address,
        "transfer_tsig_key_id": zone.transfer_tsig_key_id,
        "dnssec_enabled": zone.dnssec_enabled,
        "dnssec_algorithm": zone.dnssec_algorithm,
        "dnssec_ksk_size": zone.dnssec_ksk_size,
        "dnssec_zsk_size": zone.dnssec_zsk_size,
        "records": [_record_payload(record) for record in zone.records],
        "dnssec_keys": [
            {
                "id": key.id,
                "key_type": key.key_type,
                "algorithm": key.algorithm,
                "key_size": key.key_size,
                "key_tag": key.key_tag,
                "public_key_path": key.public_key_path,
                "private_key_path": key.private_key_path,
                "public_dnskey": key.public_dnskey,
                "ds_record": key.ds_record,
                "is_active": key.is_active,
            }
            for key in zone.dnssec_keys
        ],
    }


def _tsig_payload(key: DNSTSIGKey) -> Dict[str, Any]:
    return {
        "id": key.id,
        "name": key.name,
        "algorithm": key.algorithm,
        "secret": key.secret,
        "is_active": key.is_active,
    }


async def _load_instance_servers(db: AsyncSession, instance_id: int) -> List[DNSServer]:
    result = await db.execute(
        select(DNSServer)
        .options(
            selectinload(DNSServer.zones).selectinload(DNSZone.records),
            selectinload(DNSServer.zones).selectinload(DNSZone.dnssec_keys),
            selectinload(DNSServer.tsig_keys),
        )
        .where(DNSServer.instance_id == instance_id, DNSServer.enabled)
        .order_by(DNSServer.id)
    )
    return list(result.scalars().all())


async def build_instance_dns_payload(db: AsyncSession, instance_id: int) -> Dict[str, Any]:
    """Build the /dns/apply payload covering all enabled servers of an instance."""
    servers = await _load_instance_servers(db, instance_id)
    if not servers:
        return dict(_EMPTY_STATE_OPTIONS)

    primary = servers[0]
    payload: Dict[str, Any] = {
        "server_id": primary.id,
        "name": primary.name,
        "listening_addresses": primary.listening_addresses or ["0.0.0.0", "::"],
        "port": primary.port,
        "is_recursive": primary.is_recursive,
        "is_authoritative": primary.is_authoritative,
        "forwarders": primary.forwarders or [],
        "allow_query": primary.allow_query or ["0.0.0.0/0", "::/0"],
        "allow_transfer": primary.allow_transfer or ["127.0.0.1", "::1"],
        "also_notify": primary.also_notify or [],
        "tsig_keys": [],
        "zones": [],
    }
    for server in servers:
        payload["tsig_keys"].extend(_tsig_payload(key) for key in server.tsig_keys)
        payload["zones"].extend(_zone_payload(zone) for zone in server.zones)
    return payload


async def apply_dns_config(db: AsyncSession, instance_id: int) -> Dict[str, Any]:
    """Push the desired DNS state of an instance to its agent (synchronous)."""
    payload = await build_instance_dns_payload(db, instance_id)
    result = await agent_request(
        db=db,
        instance_id=instance_id,
        method="POST",
        path="/dns/apply",
        json_data=payload,
        service=DNS_AGENT_SERVICE,
    )
    await db.execute(
        update(DNSServer)
        .where(DNSServer.instance_id == instance_id)
        .values(status="running")
    )
    await db.commit()
    return result


async def reload_dns_agent(db: AsyncSession, instance_id: int) -> Dict[str, Any]:
    """Ask the agent to run `rndc reload` without re-applying config."""
    return await agent_request(
        db=db,
        instance_id=instance_id,
        method="POST",
        path="/dns/reload",
        service=DNS_AGENT_SERVICE,
    )


async def apply_dns_config_task(instance_id: int) -> None:
    """Background-task wrapper: own session, failures logged not raised.

    Follows the repo's firewall/mail background-dispatch pattern: the DB
    keeps the desired state, the agent converges when reachable.
    """
    async with AsyncSessionLocal() as db:
        try:
            await apply_dns_config(db, instance_id)
        except AgentClientError as exc:
            logger.error("Failed to apply DNS config on instance %s: %s", instance_id, exc)
            await db.execute(
                update(DNSServer)
                .where(DNSServer.instance_id == instance_id)
                .values(status="error")
            )
            await db.commit()
