from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit_logger import log_audit
from shared.database import get_db
from shared.models import (
    DHCPLease,
    DHCPOption,
    DHCPPool,
    DHCPReservation,
    DHCPServer,
    DHCPSubnet,
    Instance,
)
from shared.schemas import (
    DHCPLeaseReleaseResponse,
    DHCPLeaseResponse,
    DHCPOptionCreate,
    DHCPOptionResponse,
    DHCPOptionUpdate,
    DHCPPoolCreate,
    DHCPPoolResponse,
    DHCPPoolUpdate,
    DHCPReservationCreate,
    DHCPReservationResponse,
    DHCPReservationUpdate,
    DHCPServerCreate,
    DHCPServerResponse,
    DHCPServerUpdate,
    DHCPSubnetCreate,
    DHCPSubnetResponse,
    DHCPSubnetType,
    DHCPSubnetUpdate,
)
from shared.security import require_admin, require_auth

router = APIRouter()


def _validate_lease_windows(
    lease_time_min: int, lease_time_default: int, lease_time_max: int
) -> None:
    if lease_time_min > lease_time_default or lease_time_default > lease_time_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lease_time_min must be <= lease_time_default <= lease_time_max",
        )


def _validate_server_families(dhcpv4_enabled: bool, dhcpv6_enabled: bool) -> None:
    if not dhcpv4_enabled and not dhcpv6_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of dhcpv4_enabled or dhcpv6_enabled must be true",
        )


def _validate_ha_settings(ha_enabled: bool, ha_peer_address: str | None) -> None:
    if ha_enabled and not ha_peer_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ha_peer_address is required when HA is enabled",
        )


def _assert_subnet_type_allowed(server: DHCPServer, subnet_type: str) -> None:
    if subnet_type == DHCPSubnetType.V4.value and not server.dhcpv4_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DHCPv4 is disabled on this server",
        )
    if subnet_type == DHCPSubnetType.V6.value and not server.dhcpv6_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DHCPv6 is disabled on this server",
        )


@router.get("/servers/{instance_id}", response_model=List[DHCPServerResponse])
async def list_servers(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPServer).where(DHCPServer.instance_id == instance_id).order_by(DHCPServer.id)
    )
    servers = result.scalars().all()

    responses: List[DHCPServerResponse] = []
    for server in servers:
        count_result = await db.execute(
            select(func.count(DHCPSubnet.id)).where(DHCPSubnet.server_id == server.id)
        )
        item = DHCPServerResponse.model_validate(server)
        item.subnets_count = int(count_result.scalar() or 0)
        responses.append(item)
    return responses


@router.post(
    "/servers/{instance_id}",
    response_model=DHCPServerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_server(
    instance_id: int,
    data: DHCPServerCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    instance_result = await db.execute(select(Instance).where(Instance.id == instance_id))
    if not instance_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")

    _validate_server_families(data.dhcpv4_enabled, data.dhcpv6_enabled)
    _validate_ha_settings(data.ha_enabled, data.ha_peer_address)

    server = DHCPServer(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        status="stopped",
        kea_ctrl_agent_address=data.kea_ctrl_agent_address,
        kea_ctrl_agent_port=data.kea_ctrl_agent_port,
        ha_enabled=data.ha_enabled,
        ha_mode=data.ha_mode.value,
        ha_peer_address=data.ha_peer_address,
        dhcpv4_enabled=data.dhcpv4_enabled,
        dhcpv6_enabled=data.dhcpv6_enabled,
        created_by=user_id,
    )
    db.add(server)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dhcp_server",
        resource_id=server.id,
        instance_id=instance_id,
    )
    await db.refresh(server)
    return DHCPServerResponse.model_validate(server)


@router.get("/servers/detail/{server_id}", response_model=DHCPServerResponse)
async def get_server(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(select(DHCPServer).where(DHCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP server not found")
    count_result = await db.execute(
        select(func.count(DHCPSubnet.id)).where(DHCPSubnet.server_id == server.id)
    )
    response = DHCPServerResponse.model_validate(server)
    response.subnets_count = int(count_result.scalar() or 0)
    return response


@router.patch("/servers/{server_id}", response_model=DHCPServerResponse)
async def update_server(
    server_id: int,
    data: DHCPServerUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPServer).where(DHCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP server not found")

    update_data = data.model_dump(exclude_unset=True)

    dhcpv4_enabled = update_data.get("dhcpv4_enabled", server.dhcpv4_enabled)
    dhcpv6_enabled = update_data.get("dhcpv6_enabled", server.dhcpv6_enabled)
    _validate_server_families(dhcpv4_enabled, dhcpv6_enabled)

    ha_enabled = update_data.get("ha_enabled", server.ha_enabled)
    ha_peer_address = update_data.get("ha_peer_address", server.ha_peer_address)
    _validate_ha_settings(ha_enabled, ha_peer_address)

    if (
        (not dhcpv4_enabled and server.dhcpv4_enabled)
        or (not dhcpv6_enabled and server.dhcpv6_enabled)
    ):
        subnets_result = await db.execute(
            select(DHCPSubnet.id, DHCPSubnet.type).where(DHCPSubnet.server_id == server.id)
        )
        for _, subnet_type in subnets_result.all():
            if subnet_type == DHCPSubnetType.V4.value and not dhcpv4_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot disable DHCPv4 while v4 subnets exist",
                )
            if subnet_type == DHCPSubnetType.V6.value and not dhcpv6_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot disable DHCPv6 while v6 subnets exist",
                )

    for field, value in update_data.items():
        if field == "ha_mode" and value is not None:
            setattr(server, field, value.value)
        else:
            setattr(server, field, value)

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_server",
        resource_id=server.id,
        instance_id=server.instance_id,
    )
    await db.refresh(server)
    return DHCPServerResponse.model_validate(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPServer).where(DHCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP server not found")
    instance_id = server.instance_id
    await db.delete(server)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dhcp_server",
        resource_id=server_id,
        instance_id=instance_id,
    )


@router.post("/servers/{server_id}/actions/{action}")
async def server_action(
    server_id: int,
    action: str,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPServer).where(DHCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP server not found")

    allowed = {"start", "stop", "reload"}
    if action not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    if action == "start":
        server.status = "running"
    elif action == "stop":
        server.status = "stopped"

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="deploy",
        resource_type="dhcp_server",
        resource_id=server.id,
        instance_id=server.instance_id,
        new_value={"operation": action},
    )
    return {"status": "success", "action": action, "server_id": server_id}


@router.get("/servers/{server_id}/subnets", response_model=List[DHCPSubnetResponse])
async def list_subnets(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPSubnet).where(DHCPSubnet.server_id == server_id).order_by(DHCPSubnet.id)
    )
    subnets = result.scalars().all()

    responses: List[DHCPSubnetResponse] = []
    for subnet in subnets:
        pools_count = await db.execute(
            select(func.count(DHCPPool.id)).where(DHCPPool.subnet_id == subnet.id)
        )
        reservations_count = await db.execute(
            select(func.count(DHCPReservation.id)).where(DHCPReservation.subnet_id == subnet.id)
        )
        leases_count = await db.execute(
            select(func.count(DHCPLease.id)).where(DHCPLease.subnet_id == subnet.id)
        )
        item = DHCPSubnetResponse.model_validate(subnet)
        item.pools_count = int(pools_count.scalar() or 0)
        item.reservations_count = int(reservations_count.scalar() or 0)
        item.leases_count = int(leases_count.scalar() or 0)
        responses.append(item)
    return responses


@router.post(
    "/servers/{server_id}/subnets",
    response_model=DHCPSubnetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subnet(
    server_id: int,
    data: DHCPSubnetCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == server_id))
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP server not found")

    _assert_subnet_type_allowed(server, data.type.value)
    _validate_lease_windows(data.lease_time_min, data.lease_time_default, data.lease_time_max)

    subnet = DHCPSubnet(
        server_id=server_id,
        name=data.name,
        description=data.description,
        subnet=data.subnet,
        type=data.type.value,
        interface=data.interface,
        relay_addresses=data.relay_addresses,
        domain_name=data.domain_name,
        dns_servers=data.dns_servers,
        ntp_servers=data.ntp_servers,
        routers=data.routers,
        lease_time_default=data.lease_time_default,
        lease_time_max=data.lease_time_max,
        lease_time_min=data.lease_time_min,
        delegated_prefix_length=data.delegated_prefix_length,
        enabled=data.enabled,
    )
    db.add(subnet)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dhcp_subnet",
        resource_id=subnet.id,
        instance_id=server.instance_id,
    )
    await db.refresh(subnet)
    return DHCPSubnetResponse.model_validate(subnet)


@router.get("/subnets/detail/{subnet_id}", response_model=DHCPSubnetResponse)
async def get_subnet(
    subnet_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")

    pools_count = await db.execute(select(func.count(DHCPPool.id)).where(DHCPPool.subnet_id == subnet.id))
    reservations_count = await db.execute(
        select(func.count(DHCPReservation.id)).where(DHCPReservation.subnet_id == subnet.id)
    )
    leases_count = await db.execute(
        select(func.count(DHCPLease.id)).where(DHCPLease.subnet_id == subnet.id)
    )
    response = DHCPSubnetResponse.model_validate(subnet)
    response.pools_count = int(pools_count.scalar() or 0)
    response.reservations_count = int(reservations_count.scalar() or 0)
    response.leases_count = int(leases_count.scalar() or 0)
    return response


@router.patch("/subnets/{subnet_id}", response_model=DHCPSubnetResponse)
async def update_subnet(
    subnet_id: int,
    data: DHCPSubnetUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")

    update_data = data.model_dump(exclude_unset=True)

    lease_time_min = update_data.get("lease_time_min", subnet.lease_time_min)
    lease_time_default = update_data.get("lease_time_default", subnet.lease_time_default)
    lease_time_max = update_data.get("lease_time_max", subnet.lease_time_max)
    _validate_lease_windows(lease_time_min, lease_time_default, lease_time_max)

    for field, value in update_data.items():
        setattr(subnet, field, value)

    await db.commit()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_subnet",
        resource_id=subnet.id,
        instance_id=server.instance_id,
    )
    await db.refresh(subnet)
    return DHCPSubnetResponse.model_validate(subnet)


@router.delete("/subnets/{subnet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subnet(
    subnet_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await db.delete(subnet)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dhcp_subnet",
        resource_id=subnet_id,
        instance_id=server.instance_id,
    )


@router.get("/subnets/{subnet_id}/pools", response_model=List[DHCPPoolResponse])
async def list_pools(
    subnet_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPPool).where(DHCPPool.subnet_id == subnet_id).order_by(DHCPPool.id)
    )
    return [DHCPPoolResponse.model_validate(item) for item in result.scalars().all()]


@router.post(
    "/subnets/{subnet_id}/pools",
    response_model=DHCPPoolResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pool(
    subnet_id: int,
    data: DHCPPoolCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = subnet_result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")
    if data.type.value != subnet.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pool type must match subnet type",
        )

    pool = DHCPPool(
        subnet_id=subnet_id,
        start_address=data.start_address,
        end_address=data.end_address,
        type=data.type.value,
        enabled=data.enabled,
    )
    db.add(pool)
    await db.commit()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dhcp_pool",
        resource_id=pool.id,
        instance_id=server.instance_id,
    )
    await db.refresh(pool)
    return DHCPPoolResponse.model_validate(pool)


@router.patch("/pools/{pool_id}", response_model=DHCPPoolResponse)
async def update_pool(
    pool_id: int,
    data: DHCPPoolUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPPool).where(DHCPPool.id == pool_id))
    pool = result.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP pool not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(pool, field, value)

    await db.commit()
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == pool.subnet_id))
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_pool",
        resource_id=pool.id,
        instance_id=server.instance_id,
    )
    await db.refresh(pool)
    return DHCPPoolResponse.model_validate(pool)


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pool(
    pool_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPPool).where(DHCPPool.id == pool_id))
    pool = result.scalar_one_or_none()
    if not pool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP pool not found")

    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == pool.subnet_id))
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()

    await db.delete(pool)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dhcp_pool",
        resource_id=pool_id,
        instance_id=server.instance_id,
    )


@router.get("/subnets/{subnet_id}/reservations", response_model=List[DHCPReservationResponse])
async def list_reservations(
    subnet_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPReservation)
        .where(DHCPReservation.subnet_id == subnet_id)
        .order_by(DHCPReservation.id)
    )
    return [DHCPReservationResponse.model_validate(item) for item in result.scalars().all()]


@router.post(
    "/subnets/{subnet_id}/reservations",
    response_model=DHCPReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    subnet_id: int,
    data: DHCPReservationCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = subnet_result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")
    if data.type.value != subnet.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation type must match subnet type",
        )

    reservation = DHCPReservation(
        subnet_id=subnet_id,
        hostname=data.hostname,
        ip_address=data.ip_address,
        hw_address=data.hw_address,
        type=data.type.value,
        description=data.description,
    )
    db.add(reservation)
    await db.commit()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dhcp_reservation",
        resource_id=reservation.id,
        instance_id=server.instance_id,
    )
    await db.refresh(reservation)
    return DHCPReservationResponse.model_validate(reservation)


@router.patch("/reservations/{reservation_id}", response_model=DHCPReservationResponse)
async def update_reservation(
    reservation_id: int,
    data: DHCPReservationUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DHCPReservation).where(DHCPReservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DHCP reservation not found",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reservation, field, value)

    await db.commit()
    subnet_result = await db.execute(
        select(DHCPSubnet).where(DHCPSubnet.id == reservation.subnet_id)
    )
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_reservation",
        resource_id=reservation.id,
        instance_id=server.instance_id,
    )
    await db.refresh(reservation)
    return DHCPReservationResponse.model_validate(reservation)


@router.delete("/reservations/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DHCPReservation).where(DHCPReservation.id == reservation_id)
    )
    reservation = result.scalar_one_or_none()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DHCP reservation not found",
        )

    subnet_result = await db.execute(
        select(DHCPSubnet).where(DHCPSubnet.id == reservation.subnet_id)
    )
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()

    await db.delete(reservation)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dhcp_reservation",
        resource_id=reservation_id,
        instance_id=server.instance_id,
    )


@router.get("/subnets/{subnet_id}/options", response_model=List[DHCPOptionResponse])
async def list_options(
    subnet_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPOption).where(DHCPOption.subnet_id == subnet_id).order_by(DHCPOption.id)
    )
    return [DHCPOptionResponse.model_validate(item) for item in result.scalars().all()]


@router.post(
    "/subnets/{subnet_id}/options",
    response_model=DHCPOptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_option(
    subnet_id: int,
    data: DHCPOptionCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == subnet_id))
    subnet = subnet_result.scalar_one_or_none()
    if not subnet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP subnet not found")
    if data.type.value != subnet.type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Option type must match subnet type",
        )

    option = DHCPOption(
        subnet_id=subnet_id,
        option_code=data.option_code,
        option_name=data.option_name,
        option_value=data.option_value,
        type=data.type.value,
    )
    db.add(option)
    await db.commit()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dhcp_option",
        resource_id=option.id,
        instance_id=server.instance_id,
    )
    await db.refresh(option)
    return DHCPOptionResponse.model_validate(option)


@router.patch("/options/{option_id}", response_model=DHCPOptionResponse)
async def update_option(
    option_id: int,
    data: DHCPOptionUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPOption).where(DHCPOption.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP option not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(option, field, value)

    await db.commit()
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == option.subnet_id))
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_option",
        resource_id=option.id,
        instance_id=server.instance_id,
    )
    await db.refresh(option)
    return DHCPOptionResponse.model_validate(option)


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option(
    option_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPOption).where(DHCPOption.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP option not found")

    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == option.subnet_id))
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()

    await db.delete(option)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dhcp_option",
        resource_id=option_id,
        instance_id=server.instance_id,
    )


@router.get("/subnets/{subnet_id}/leases", response_model=List[DHCPLeaseResponse])
async def list_subnet_leases(
    subnet_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPLease)
        .where(DHCPLease.subnet_id == subnet_id)
        .order_by(DHCPLease.ip_address.asc())
    )
    return [DHCPLeaseResponse.model_validate(item) for item in result.scalars().all()]


@router.get("/leases/active", response_model=List[DHCPLeaseResponse])
async def list_active_leases(
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DHCPLease)
        .where(DHCPLease.state == "active")
        .order_by(DHCPLease.id.desc())
    )
    return [DHCPLeaseResponse.model_validate(item) for item in result.scalars().all()]


@router.delete("/leases/{lease_id}", response_model=DHCPLeaseReleaseResponse)
async def release_lease(
    lease_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DHCPLease).where(DHCPLease.id == lease_id))
    lease = result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DHCP lease not found")

    lease.state = "released"
    now = datetime.utcnow()
    lease.released_at = now
    lease.lease_end = now

    await db.commit()
    subnet_result = await db.execute(select(DHCPSubnet).where(DHCPSubnet.id == lease.subnet_id))
    subnet = subnet_result.scalar_one()
    server_result = await db.execute(select(DHCPServer).where(DHCPServer.id == subnet.server_id))
    server = server_result.scalar_one()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dhcp_lease",
        resource_id=lease.id,
        instance_id=server.instance_id,
        new_value={"state": "released"},
    )
    await db.refresh(lease)
    return DHCPLeaseReleaseResponse(id=lease.id, state=lease.state, released_at=lease.released_at)
