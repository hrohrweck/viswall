"""Compose the desired firewall/VPN state of an instance and push it to agents.

Single source of truth for the gateway -> agent payload contracts consumed by
the firewall-service agent (``POST /firewall/apply``, plan todo 8) and the
vpn-service agent (``POST /vpn/apply``, plan todo 16). No router imports this
module yet; todos 19/20/24 wire it into the routers.

Payload schema (``json_data`` of ``POST /firewall/apply``)
-----------------------------------------------------------
::

    {
      "interfaces": [                    # NetworkInterface rows (enabled only)
        {
          "id": int,
          "name": str,                   # e.g. "enp0s31f6", "docker0"
          "type": str|null,              # wan | lan | dmz | other
          "config_type": str|null,       # dhcp | static
          "ip_address": str|null,
          "netmask": str|null,
          "gateway": str|null,
          "mtu": int|null,
          "bandwidth_in": int|null,      # kbps
          "bandwidth_out": int|null,     # kbps
          "description": str|null,
          # todo 21 columns - guarded, present only when the row has them:
          "ipv6_address": str|null,
          "ipv6_gateway": str|null,
          "dns_servers": [str, ...],
          "routes": [{"to": str, "via": str|null, "on_link": bool}, ...]
        }, ...
      ],
      "rules": [                         # FirewallRule rows (enabled, order_index)
        {
          "id": int,
          "name": str,
          "source_type": str|null,       # any | host | network | range
          "source_value": str|null,
          "dest_type": str|null,
          "dest_value": str|null,
          "service_protocol": str|null,  # tcp | udp | icmp | any
          "service_ports": str|null,     # raw string, e.g. "22" / "8000-8100"
          "action": str,                 # accept | drop | reject
          "log_enabled": bool,
          "order_index": int,
          # extension keys the agent dataclass defines; the columns arrive in
          # todo 21 (limit) / later (interface_in/out), so they are guarded:
          "limit": str|null,             # e.g. "10/minute burst 5 packets"
          "interface_in": str|null,
          "interface_out": str|null
        }, ...
      ],
      "nat_rules": [                     # NATRule rows (enabled, order_index)
        {
          "id": int,
          "name": str,
          "type": str,                   # snat | dnat | masquerade
          "interface": str|null,
          "source_network": str|null,
          "dest_network": str|null,
          "to_source": str|null,
          "to_destination": str|null,
          "service_protocol": str|null,
          "service_ports": str|null,
          "order_index": int
        }, ...
      ],
      "routing_rules": [                 # RoutingRule rows (enabled, order_index)
        {
          "id": int,
          "name": str,
          "source_network": str|null,
          "dest_network": str|null,
          "service": str|null,
          "inbound_interface": str|null,
          "gateway": str|null,
          "outbound_interface": str|null,
          "mark": int|null,              # fwmark
          "order_index": int
        }, ...
      ],
      "qos": [                           # QoSPolicy rows (enabled), one per iface
        {
          "id": int,
          "name": str,
          "interface": str,              # policy.interface_name
          "algorithm": str,              # cake | fq_codel | htb
          "download_kbps": int,
          "upload_kbps": int,
          "classes": [                   # QoSClass children, priority order
            {
              "id": int,
              "name": str,
              "priority": int,           # 1 = highest
              "min_rate_kbps": int,
              "max_rate_kbps": int,
              "match_ports": [int, ...]|null,
              "match_dscp": str|null,    # e.g. "EF", "AF41"
              "match_protocol": str      # tcp | udp | any
            }, ...
          ]
        }, ...
      ]
    }

Payload schema (``json_data`` of ``POST /vpn/apply``)
-----------------------------------------------------
Built from the first enabled VPNServer whose ``tunnel_type`` is ``client`` or
``site-to-site`` (the column arrives in todo 23; rows without it are skipped).
Returns ``{}`` when no such tunnel is defined::

    {
      "protocol": str,                   # e.g. "wireguard"
      "name": str,
      "address": str|null,               # local_address (todo 23)
      "private_key": str|null,           # todo 23, client tunnels only
      "endpoint": str|null,              # todo 23
      "peer_public_key": str|null,       # todo 23
      "allowed_ips": str|null,           # todo 23, e.g. "10.80.0.0/16"
      "persistent_keepalive": int|null   # todo 23
    }

Keys whose value is ``None`` are omitted (the agents treat a missing optional
field exactly like an explicit null), which also keeps the emitted JSON
deterministic for golden tests.

Unlike dns_dispatch there is no single status column spanning all firewall
tables, so ``apply_firewall_config`` does not write any state back to the DB;
the database stays the desired-state store and the audit log records the
dispatch outcome. The DB keeps rows the agent could not apply (desired-state
model), the background-task wrapper only logs the failure.
"""

import logging
from typing import Any, Dict, List

# allow: SIZE_OK - the plan mandates exactly ONE file for these payload
# contracts and the JSON schema docstring above is the documented
# single-source-of-truth; the remaining code is declarative row->dict
# serializers mirroring dns_dispatch, with no second responsibility.


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import AsyncSessionLocal
from shared.models import (
    FirewallRule,
    NATRule,
    NetworkInterface,
    QoSPolicy,
    RoutingRule,
    VPNServer,
)
from utils.agent_client import AgentClientError, agent_request, log_agent_dispatch

logger = logging.getLogger(__name__)

FIREWALL_AGENT_SERVICE = "firewall"
VPN_AGENT_SERVICE = "vpn"


def _drop_none(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None-valued keys so optional fields stay absent from the JSON."""
    return {key: value for key, value in mapping.items() if value is not None}


def _interface_payload(iface: NetworkInterface) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": iface.id,
            "name": iface.name,
            "type": iface.type,
            "config_type": iface.config_type,
            "ip_address": iface.ip_address,
            "netmask": iface.netmask,
            "gateway": iface.gateway,
            "mtu": iface.mtu,
            "bandwidth_in": iface.bandwidth_in,
            "bandwidth_out": iface.bandwidth_out,
            "description": iface.description,
            # todo 21 columns - guarded so this module runs before they exist.
            "ipv6_address": getattr(iface, "ipv6_address", None),
            "ipv6_gateway": getattr(iface, "ipv6_gateway", None),
            "dns_servers": getattr(iface, "dns_servers", None),
            "routes": getattr(iface, "routes", None),
        }
    )


def _rule_payload(rule: FirewallRule) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": rule.id,
            "name": rule.name,
            "source_type": rule.source_type,
            "source_value": rule.source_value,
            "dest_type": rule.dest_type,
            "dest_value": rule.dest_value,
            "service_protocol": rule.service_protocol,
            "service_ports": rule.service_ports,
            "action": rule.action,
            "log_enabled": rule.log_enabled,
            "order_index": rule.order_index,
            # Agent dataclass extension fields; columns land in todo 21+.
            "limit": getattr(rule, "limit", None),
            "interface_in": getattr(rule, "interface_in", None),
            "interface_out": getattr(rule, "interface_out", None),
        }
    )


def _nat_payload(nat: NATRule) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": nat.id,
            "name": nat.name,
            "type": nat.type,
            "interface": nat.interface,
            "source_network": nat.source_network,
            "dest_network": nat.dest_network,
            "to_source": nat.to_source,
            "to_destination": nat.to_destination,
            "service_protocol": nat.service_protocol,
            "service_ports": nat.service_ports,
            "order_index": nat.order_index,
        }
    )


def _routing_payload(route: RoutingRule) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": route.id,
            "name": route.name,
            "source_network": route.source_network,
            "dest_network": route.dest_network,
            "service": route.service,
            "inbound_interface": route.inbound_interface,
            "gateway": route.gateway,
            "outbound_interface": route.outbound_interface,
            "mark": route.mark,
            "order_index": route.order_index,
        }
    )


def _qos_class_payload(qos_class: Any) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": qos_class.id,
            "name": qos_class.name,
            "priority": qos_class.priority,
            "min_rate_kbps": qos_class.min_rate_kbps,
            "max_rate_kbps": qos_class.max_rate_kbps,
            "match_ports": qos_class.match_ports,
            "match_dscp": qos_class.match_dscp,
            "match_protocol": qos_class.match_protocol,
        }
    )


def _qos_payload(policy: QoSPolicy) -> Dict[str, Any]:
    return _drop_none(
        {
            "id": policy.id,
            "name": policy.name,
            "interface": policy.interface_name,
            "algorithm": policy.algorithm,
            "download_kbps": policy.download_kbps,
            "upload_kbps": policy.upload_kbps,
            "classes": [_qos_class_payload(cls_) for cls_ in policy.classes],
        }
    )


def _compose_firewall_payload(
    interfaces: List[NetworkInterface],
    rules: List[FirewallRule],
    nat_rules: List[NATRule],
    routing_rules: List[RoutingRule],
    qos_policies: List[QoSPolicy],
) -> Dict[str, Any]:
    """Pure composition of the /firewall/apply body from row lists.

    Split from the DB loader so golden-payload tests can feed plain
    dataclass-like rows without a database.
    """
    return {
        "interfaces": [_interface_payload(iface) for iface in interfaces],
        "rules": [_rule_payload(rule) for rule in rules],
        "nat_rules": [_nat_payload(nat) for nat in nat_rules],
        "routing_rules": [_routing_payload(route) for route in routing_rules],
        "qos": [_qos_payload(policy) for policy in qos_policies],
    }


async def _load_enabled_rows(
    db: AsyncSession, model: Any, instance_id: int, order_by: tuple, options: tuple = ()
) -> List[Any]:
    """Load the enabled rows of ``model`` for an instance, in a fixed order."""
    result = await db.execute(
        select(model)
        .options(*options)
        .where(model.instance_id == instance_id, model.enabled.is_(True))
        .order_by(*order_by)
    )
    return list(result.scalars().all())


async def _load_rows(db: AsyncSession, instance_id: int) -> tuple:
    """Load every enabled firewall-related row for an instance, ordered."""
    return (
        await _load_enabled_rows(
            db, FirewallRule, instance_id, (FirewallRule.order_index, FirewallRule.id)
        ),
        await _load_enabled_rows(
            db, NATRule, instance_id, (NATRule.order_index, NATRule.id)
        ),
        await _load_enabled_rows(
            db, RoutingRule, instance_id, (RoutingRule.order_index, RoutingRule.id)
        ),
        await _load_enabled_rows(
            db, QoSPolicy, instance_id, (QoSPolicy.id,),
            (selectinload(QoSPolicy.classes),),
        ),
        await _load_enabled_rows(
            db, NetworkInterface, instance_id, (NetworkInterface.id,)
        ),
    )


async def build_instance_firewall_payload(
    db: AsyncSession, instance_id: int
) -> Dict[str, Any]:
    """Build the /firewall/apply payload covering all enabled rows of an instance."""
    rules, nat_rules, routing_rules, qos_policies, interfaces = await _load_rows(
        db, instance_id
    )
    return _compose_firewall_payload(
        interfaces=interfaces,
        rules=rules,
        nat_rules=nat_rules,
        routing_rules=routing_rules,
        qos_policies=qos_policies,
    )


async def build_instance_vpn_payload(
    db: AsyncSession, instance_id: int
) -> Dict[str, Any]:
    """Build the /vpn/apply payload from the instance's site-to-site tunnel.

    Returns ``{}`` when no enabled VPNServer has ``tunnel_type``
    ``client``/``site-to-site`` (todo 23 column; rows without it are skipped).
    """
    servers = (
        await db.execute(
            select(VPNServer)
            .where(
                VPNServer.instance_id == instance_id,
                VPNServer.enabled.is_(True),
            )
            .order_by(VPNServer.id)
        )
    ).scalars().all()
    for server in servers:
        if getattr(server, "tunnel_type", None) not in ("client", "site-to-site"):
            continue
        return _drop_none(
            {
                "protocol": server.protocol,
                "name": server.name,
                "address": getattr(server, "local_address", None),
                "private_key": getattr(server, "private_key", None),
                "endpoint": getattr(server, "endpoint", None),
                "peer_public_key": getattr(server, "peer_public_key", None),
                "allowed_ips": getattr(server, "allowed_ips", None),
                "persistent_keepalive": getattr(
                    server, "persistent_keepalive", None
                ),
            }
        )
    return {}


async def apply_firewall_config(
    db: AsyncSession, instance_id: int, user_id: int = None
) -> Dict[str, Any]:
    """Push the desired firewall state of an instance to its agent (synchronous).

    Raises AgentClientError when the agent is unreachable; the DB row was
    already persisted by the caller (desired-state model, mirror dns_dispatch).
    """
    payload = await build_instance_firewall_payload(db, instance_id)
    try:
        result = await agent_request(
            db=db,
            instance_id=instance_id,
            method="POST",
            path="/firewall/apply",
            json_data=payload,
            service=FIREWALL_AGENT_SERVICE,
        )
    except AgentClientError as exc:
        await log_agent_dispatch(
            db, instance_id=instance_id, resource_type="firewall_agent",
            action="deploy", path="/firewall/apply", ok=False, detail=str(exc),
            user_id=user_id,
        )
        raise
    await log_agent_dispatch(
        db, instance_id=instance_id, resource_type="firewall_agent",
        action="deploy", path="/firewall/apply", ok=True, user_id=user_id,
    )
    return result


async def apply_vpn_config(
    db: AsyncSession, instance_id: int, user_id: int = None
) -> Dict[str, Any]:
    """Push the desired site-to-site tunnel state to the vpn agent (synchronous)."""
    payload = await build_instance_vpn_payload(db, instance_id)
    try:
        result = await agent_request(
            db=db,
            instance_id=instance_id,
            method="POST",
            path="/vpn/apply",
            json_data=payload,
            service=VPN_AGENT_SERVICE,
        )
    except AgentClientError as exc:
        await log_agent_dispatch(
            db, instance_id=instance_id, resource_type="vpn_agent",
            action="deploy", path="/vpn/apply", ok=False, detail=str(exc),
            user_id=user_id,
        )
        raise
    await log_agent_dispatch(
        db, instance_id=instance_id, resource_type="vpn_agent",
        action="deploy", path="/vpn/apply", ok=True, user_id=user_id,
    )
    return result


async def apply_firewall_config_task(instance_id: int) -> None:
    """Background-task wrapper: own session, failures logged not raised.

    Follows the dns_dispatch background pattern: the DB keeps the desired
    state and the agent converges when reachable; a failed dispatch is
    logged (and audit-logged by apply_firewall_config) without raising into
    FastAPI's BackgroundTasks runner.
    """
    async with AsyncSessionLocal() as db:
        try:
            await apply_firewall_config(db, instance_id)
        except AgentClientError as exc:
            logger.error(
                "Failed to apply firewall config on instance %s: %s",
                instance_id, exc,
            )
