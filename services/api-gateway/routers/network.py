"""Host interface configuration management.

Desired state lives in the network_interfaces table; the node agent
(container on the host network namespace) applies it live and persists
it as netplan. CRUD stays DB-only — hitting "Apply" is the explicit
step that dispatches to the agent, mirroring the routing rule workflow.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
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
    desired state as a netplan file.
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
            }
            for i in configured
        ],
        "force": data.force,
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

    return InterfaceApplyResultResponse.model_validate(result)
