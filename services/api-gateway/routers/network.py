"""Host interface configuration management.

Desired state lives in the network_interfaces table; the node agent
(container on the host network namespace) applies it live and persists
it as netplan. CRUD stays DB-only — hitting "Apply" is the explicit
step that dispatches to the agent, mirroring the routing rule workflow.
"""

import ipaddress
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.models import Instance, NetworkInterface, User
from shared.schemas import (
    InterfaceApplyRequest,
    InterfaceApplyResultResponse,
    InterfaceLiveStateResponse,
    NetworkInterfaceCreate,
    NetworkInterfaceResponse,
    NetworkInterfaceUpdate,
)
from shared.security import require_admin, require_auth
from shared.audit_logger import log_audit
from utils.agent_client import (
    AgentClientError,
    AgentConnectionError,
    AgentResponseError,
    agent_request,
    log_agent_dispatch,
)

router = APIRouter()

AGENT_SERVICE = "node"  # key in Instance.config["agent_endpoints"]


async def _instance_for_user(
    db: AsyncSession, instance_id: int, user_id: int
) -> Instance:
    """Load the instance, enforcing the same access rules as instances.py."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    instance = await db.scalar(select(Instance).where(Instance.id == instance_id))
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")

    if user.role != "superadmin" and instance_id not in (user.instances or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this instance"
        )
    return instance


async def _interface_or_404(db: AsyncSession, interface_id: int) -> NetworkInterface:
    interface = await db.scalar(
        select(NetworkInterface).where(NetworkInterface.id == interface_id)
    )
    if not interface:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interface not found"
        )
    return interface


def _netmask_from_prefixlen(prefixlen: int) -> str:
    """Dotted-quad netmask for an IPv4 prefix length (24 -> 255.255.255.0)."""
    return str(ipaddress.IPv4Network(f"0.0.0.0/{prefixlen}").netmask)


def _parse_live_rows(result: object) -> list[dict]:
    """Normalize the node-agent GET /interfaces payload into upsert rows.

    Raises TypeError/ValueError for a structurally malformed agent
    response so the caller can map it to a 502 instead of a 500.
    """
    if not isinstance(result, dict):
        raise TypeError("agent response is not an object")
    interfaces = result.get("interfaces")
    if not isinstance(interfaces, list):
        raise TypeError("agent response lacks an 'interfaces' list")
    default_gateway = result.get("default_gateway")

    rows: list[dict] = []
    for raw in interfaces:
        if not isinstance(raw, dict):
            raise TypeError("interface entry is not an object")
        name = raw.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("interface entry lacks a valid 'name'")

        ip_address = None
        netmask = None
        for addr in raw.get("addresses") or []:
            if not isinstance(addr, dict) or addr.get("family", "inet") != "inet":
                continue
            addr_str = addr.get("address")
            prefix = addr.get("prefixlen")
            if not isinstance(addr_str, str) or not isinstance(prefix, int):
                continue
            try:
                netmask = _netmask_from_prefixlen(prefix)
            except ValueError:
                continue
            ip_address = addr_str
            break

        gateway = (
            default_gateway
            if raw.get("has_default_route") is True and isinstance(default_gateway, str)
            else None
        )
        mtu = raw.get("mtu") if isinstance(raw.get("mtu"), int) else None
        rows.append(
            {
                "name": name,
                "ip_address": ip_address,
                "netmask": netmask,
                "gateway": gateway,
                "mtu": mtu,
            }
        )
    return rows


async def _upsert_live_interfaces(
    db: AsyncSession, instance_id: int, rows: list[dict]
) -> tuple[int, int]:
    """Upsert NetworkInterface rows by name from live discovery rows.

    Creates rows the DB does not know yet and refreshes ip/netmask/gateway/
    mtu on existing rows; never deletes rows the agent no longer reports.
    """
    existing = {
        iface.name: iface
        for iface in (
            await db.scalars(
                select(NetworkInterface).where(NetworkInterface.instance_id == instance_id)
            )
        ).all()
    }
    created = 0
    updated = 0
    for row in rows:
        name = row["name"]
        if name == "lo":
            continue  # the agent refuses to manage loopback; never store it
        values = {field: row.get(field) for field in ("ip_address", "netmask", "gateway", "mtu")}
        iface = existing.get(name)
        if iface is None:
            db.add(
                NetworkInterface(
                    instance_id=instance_id,
                    name=name,
                    type="other",
                    config_type="dhcp",
                    enabled=True,
                    **values,
                )
            )
            created += 1
            continue
        changed = False
        for field, value in values.items():
            if getattr(iface, field) != value:
                setattr(iface, field, value)
                changed = True
        if changed:
            updated += 1
    return created, updated


@router.get("/interfaces/{instance_id}", response_model=List[NetworkInterfaceResponse])
async def list_interfaces(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Configured (desired-state) interfaces for an instance."""
    await _instance_for_user(db, instance_id, user_id)
    interfaces = (
        await db.scalars(
            select(NetworkInterface)
            .where(NetworkInterface.instance_id == instance_id)
            .order_by(NetworkInterface.name)
        )
    ).all()
    return [NetworkInterfaceResponse.model_validate(i) for i in interfaces]


@router.post(
    "/interfaces/{instance_id}",
    response_model=NetworkInterfaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_interface(
    instance_id: int,
    data: NetworkInterfaceCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add an interface to the instance's desired configuration."""
    await _instance_for_user(db, instance_id, user_id)

    existing = await db.scalar(
        select(NetworkInterface).where(
            NetworkInterface.instance_id == instance_id,
            NetworkInterface.name == data.name,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Interface {data.name} is already configured for this instance",
        )

    interface = NetworkInterface(instance_id=instance_id, **data.model_dump())
    db.add(interface)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="network_interface",
        resource_id=interface.id,
        instance_id=instance_id,
        new_value={"name": interface.name, "config_type": interface.config_type},
    )
    await db.refresh(interface)
    return NetworkInterfaceResponse.model_validate(interface)


@router.patch("/interfaces/detail/{interface_id}", response_model=NetworkInterfaceResponse)
async def update_interface(
    interface_id: int,
    data: NetworkInterfaceUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update desired state for one interface (apply separately)."""
    interface = await _interface_or_404(db, interface_id)
    await _instance_for_user(db, interface.instance_id, user_id)

    update_data = data.model_dump(exclude_unset=True)
    if update_data.get("name") and update_data["name"] != interface.name:
        clash = await db.scalar(
            select(NetworkInterface).where(
                NetworkInterface.instance_id == interface.instance_id,
                NetworkInterface.name == update_data["name"],
            )
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Interface {update_data['name']} is already configured for this instance",
            )

    for field, value in update_data.items():
        setattr(interface, field, value)

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="network_interface",
        resource_id=interface.id,
        instance_id=interface.instance_id,
        new_value=update_data,
    )
    await db.refresh(interface)
    return NetworkInterfaceResponse.model_validate(interface)


@router.delete("/interfaces/detail/{interface_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interface(
    interface_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove an interface from the instance's desired configuration."""
    interface = await _interface_or_404(db, interface_id)
    await _instance_for_user(db, interface.instance_id, user_id)

    await db.delete(interface)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="network_interface",
        resource_id=interface.id,
        instance_id=interface.instance_id,
    )
    return None


@router.get("/interfaces/{instance_id}/live", response_model=InterfaceLiveStateResponse)
async def live_interfaces(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Live interface state as reported by the instance's node agent."""
    await _instance_for_user(db, instance_id, user_id)
    try:
        result = await agent_request(db, instance_id, "GET", "/interfaces", service=AGENT_SERVICE)
    except AgentConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Node agent unreachable — is the node-agent container running on this host?",
        ) from exc
    except AgentResponseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except AgentClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    return InterfaceLiveStateResponse.model_validate(result)


@router.post("/interfaces/{instance_id}/refresh")
async def refresh_interfaces(
    instance_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Refresh desired-state rows from live host discovery (no apply).

    GET /interfaces on the node agent, upsert NetworkInterface rows by
    name (create missing, update ip/netmask/gateway/mtu, never delete),
    and audit-log the refresh. Applying the refreshed state stays an
    explicit /interfaces/{instance_id}/apply call.
    """
    await _instance_for_user(db, instance_id, user_id)

    try:
        result = await agent_request(db, instance_id, "GET", "/interfaces", service=AGENT_SERVICE)
    except AgentConnectionError as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="refresh",
            path="/interfaces",
            ok=False,
            detail=f"node agent unreachable: {exc}",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Node agent unreachable — is the node-agent container running on this host?",
        ) from exc
    except (AgentResponseError, AgentClientError) as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="refresh",
            path="/interfaces",
            ok=False,
            detail=str(exc),
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    try:
        rows = _parse_live_rows(result)
    except (ValueError, TypeError) as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="refresh",
            path="/interfaces",
            ok=False,
            detail=f"malformed agent response: {exc}",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Node agent returned a malformed interface list: {exc}",
        ) from exc

    created, updated = await _upsert_live_interfaces(db, instance_id, rows)
    await db.commit()
    await log_agent_dispatch(
        db,
        instance_id=instance_id,
        resource_type="network_interface",
        action="refresh",
        path="/interfaces",
        ok=True,
        detail=f"{created} created, {updated} updated",
        user_id=user_id,
    )
    return {
        "created": created,
        "updated": updated,
        "interfaces": [row["name"] for row in rows],
    }


@router.post(
    "/interfaces/{instance_id}/apply",
    response_model=InterfaceApplyResultResponse,
)
async def apply_interfaces(
    instance_id: int,
    data: InterfaceApplyRequest,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dispatch the desired interface configuration to the node agent.

    The agent plans idempotent netlink changes, refuses anything that
    would cut the default route without force=true, and persists the
    desired state as a netplan file. With try_mode=true the agent runs
    `netplan try` and confirms only after its health probes pass; the
    probe results and netplan outcome (accepted/reverted/error) are
    relayed verbatim in the response.
    """
    await _instance_for_user(db, instance_id, user_id)

    configured = (
        await db.scalars(
            select(NetworkInterface).where(
                NetworkInterface.instance_id == instance_id
            )
        )
    ).all()

    payload = {
        "interfaces": [
            {
                "name": i.name,
                "config_type": i.config_type,
                "ip_address": i.ip_address,
                "netmask": i.netmask,
                "gateway": i.gateway,
                "mtu": i.mtu,
                "enabled": bool(i.enabled),
                # todo-21 fields, getattr-guarded (task requirement) so the
                # builder works before the column migration has been applied.
                "ipv6_address": getattr(i, "ipv6_address", None),
                "ipv6_gateway": getattr(i, "ipv6_gateway", None),
                "dns_servers": getattr(i, "dns_servers", None) or [],
                "routes": getattr(i, "routes", None) or [],
            }
            for i in configured
        ],
        "force": data.force,
        # todo-9 try-mode flag, getattr-guarded: InterfaceApplyRequest only
        # defines `force` today (todo 23 extends the schema).
        "try_mode": getattr(data, "try_mode", False),
    }

    try:
        result = await agent_request(
            db, instance_id, "POST", "/interfaces/apply", json_data=payload, service=AGENT_SERVICE
        )
    except AgentConnectionError as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="apply",
            path="/interfaces/apply",
            ok=False,
            detail=f"node agent unreachable: {exc}",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Node agent unreachable — is the node-agent container running on this host?",
        ) from exc
    except AgentResponseError as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="apply",
            path="/interfaces/apply",
            ok=False,
            detail=str(exc),
            user_id=user_id,
        )
        if exc.status_code == 400:
            # WAN guardrail (todo 9) or payload validation refused the plan.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            ) from exc
        if exc.status_code == 409:
            # The agent refused a plan that would cut the default route.
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc
    except AgentClientError as exc:
        await log_agent_dispatch(
            db,
            instance_id=instance_id,
            resource_type="network_interface",
            action="apply",
            path="/interfaces/apply",
            ok=False,
            detail=str(exc),
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    await log_agent_dispatch(
        db,
        instance_id=instance_id,
        resource_type="network_interface",
        action="apply",
        path="/interfaces/apply",
        ok=bool(result.get("success")),
        detail=result.get("message", ""),
        user_id=user_id,
    )

    # Passthrough: the agent's ApplyResult carries try_mode, probes and
    # netplan_outcome (accepted/reverted/error). InterfaceApplyResultResponse
    # does not model those fields yet, so re-validating through the
    # response_model would strip them; a JSONResponse bypasses that.
    return JSONResponse(content=result)
