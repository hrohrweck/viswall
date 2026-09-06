import base64
import hashlib
import ipaddress
import secrets
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit_logger import log_audit
from shared.database import get_db
from shared.models import DNSRecord, DNSServer, DNSZone, DNSZoneSlave, Instance
from utils.agent_client import AgentClientError
from utils.dns_dispatch import (
    apply_dns_config,
    apply_dns_config_task,
    reload_dns_agent,
)
from shared.schemas import (
    BulkRecordImport,
    CreatePTRRequest,
    CreateReverseZoneRequest,
    DNSRecordCreate,
    DNSRecordResponse,
    DNSRecordType,
    DNSRecordUpdate,
    DNSServerCreate,
    DNSServerResponse,
    DNSServerUpdate,
    DNSZoneCreate,
    DNSZoneResponse,
    DNSZoneSlaveResponse,
    DNSZoneType,
    DNSZoneUpdate,
    DNSTSIGKeyCreate,
    DNSTSIGKeyResponse,
    DNSTSIGKeyRotate,
    DNSSECRolloverRequest,
    DNSSECKeyResponse,
)
from shared.security import require_admin, require_auth

from shared.models import DNSTSIGKey, DNSSECKey

router = APIRouter()


def _serial_from_now() -> int:
    return int(datetime.utcnow().strftime("%Y%m%d%H"))


def _ensure_fqdn(value: str) -> str:
    return value if value.endswith(".") else f"{value}."


def _generate_tsig_secret(algorithm: str) -> str:
    if algorithm == "hmac-sha512":
        size = 64
    else:
        size = 32
    return base64.b64encode(secrets.token_bytes(size)).decode("ascii")


def _dnskey_line(zone_name: str, key_tag: int, algorithm: str) -> str:
    seed = f"{zone_name}:{key_tag}:{algorithm}:{secrets.token_hex(8)}"
    blob = base64.b64encode(hashlib.sha256(seed.encode("utf-8")).digest()).decode("ascii")
    return f"{zone_name}. 3600 IN DNSKEY 257 3 13 {blob}"


def _ds_line(zone_name: str, key_tag: int, dnskey: str) -> str:
    digest = hashlib.sha256(dnskey.encode("utf-8")).hexdigest().upper()
    return f"{zone_name}. IN DS {key_tag} 13 2 {digest}"


def _new_key_tag(zone_name: str, key_type: str, key_size: int) -> int:
    source = f"{zone_name}:{key_type}:{key_size}:{secrets.token_hex(6)}"
    return (abs(hash(source)) % 64511) + 1024


def _reverse_zone_name(network: str) -> str:
    net = ipaddress.ip_network(network, strict=False)

    if isinstance(net, ipaddress.IPv4Network):
        if net.prefixlen % 8 != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IPv4 reverse zones must use /8, /16, /24 or /32 boundaries",
            )
        octets = str(net.network_address).split(".")[: net.prefixlen // 8]
        return f"{'.'.join(reversed(octets))}.in-addr.arpa"

    if net.prefixlen % 4 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IPv6 reverse zones must use nibble (/4) boundaries",
        )
    expanded = net.network_address.exploded.replace(":", "")
    nibbles = list(expanded[: net.prefixlen // 4])
    return f"{'.'.join(reversed(nibbles))}.ip6.arpa"


def _ptr_name_for_zone(ip_address: str, zone_name: str) -> str:
    pointer = ipaddress.ip_address(ip_address).reverse_pointer
    suffix = zone_name.rstrip(".")
    if not pointer.endswith(suffix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="IP address does not belong to this reverse zone",
        )
    relative = pointer[: -len(suffix)].rstrip(".")
    return relative or "@"


def _schedule_apply(background_tasks: BackgroundTasks, instance_id) -> None:
    """Queue an agent config push after the response is sent (repo pattern)."""
    if instance_id is not None:
        background_tasks.add_task(apply_dns_config_task, instance_id)


async def _server_instance_id(db: AsyncSession, server_id: int):
    result = await db.execute(
        select(DNSServer.instance_id).where(DNSServer.id == server_id)
    )
    return result.scalar_one_or_none()


async def _zone_instance_id(db: AsyncSession, zone_id: int):
    result = await db.execute(
        select(DNSServer.instance_id)
        .join(DNSZone, DNSZone.server_id == DNSServer.id)
        .where(DNSZone.id == zone_id)
    )
    return result.scalar_one_or_none()


async def _record_instance_id(db: AsyncSession, record: DNSRecord):
    return await _zone_instance_id(db, record.zone_id)


@router.get("/servers/{instance_id}", response_model=List[DNSServerResponse])
async def list_servers(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSServer).where(DNSServer.instance_id == instance_id).order_by(DNSServer.id)
    )
    servers = result.scalars().all()

    responses: List[DNSServerResponse] = []
    for server in servers:
        count_result = await db.execute(
            select(func.count(DNSZone.id)).where(DNSZone.server_id == server.id)
        )
        item = DNSServerResponse.model_validate(server)
        item.zones_count = int(count_result.scalar() or 0)
        responses.append(item)
    return responses


@router.post(
    "/servers/{instance_id}",
    response_model=DNSServerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_server(
    instance_id: int,
    data: DNSServerCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    instance = await db.execute(select(Instance).where(Instance.id == instance_id))
    if not instance.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")

    server = DNSServer(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        listening_addresses=data.listening_addresses,
        port=data.port,
        is_recursive=data.is_recursive,
        is_authoritative=data.is_authoritative,
        forwarders=data.forwarders,
        allow_query=data.allow_query,
        allow_transfer=data.allow_transfer,
        also_notify=data.also_notify,
        dnssec_enabled=data.dnssec_enabled,
        created_by=user_id,
        status="stopped",
    )
    db.add(server)
    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dns_server",
        resource_id=server.id,
        instance_id=instance_id,
    )
    await db.refresh(server)
    _schedule_apply(background_tasks, instance_id)
    return DNSServerResponse.model_validate(server)


@router.get("/servers/detail/{server_id}", response_model=DNSServerResponse)
async def get_server(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")
    count_result = await db.execute(
        select(func.count(DNSZone.id)).where(DNSZone.server_id == server.id)
    )
    response = DNSServerResponse.model_validate(server)
    response.zones_count = int(count_result.scalar() or 0)
    return response


@router.patch("/servers/{server_id}", response_model=DNSServerResponse)
async def update_server(
    server_id: int,
    data: DNSServerUpdate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(server, field, value)

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dns_server",
        resource_id=server.id,
        instance_id=server.instance_id,
    )
    await db.refresh(server)
    _schedule_apply(background_tasks, server.instance_id)
    return DNSServerResponse.model_validate(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")
    instance_id = server.instance_id
    await db.delete(server)
    await db.commit()
    _schedule_apply(background_tasks, instance_id)
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dns_server",
        resource_id=server_id,
        instance_id=instance_id,
    )


@router.post("/servers/{server_id}/actions/{action}")
async def server_action(
    server_id: int,
    action: str,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")

    allowed = {"start", "stop", "reload", "apply"}
    if action not in allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    agent_result = None
    if action == "start":
        server.status = "running"
        _schedule_apply(background_tasks, server.instance_id)
    elif action == "stop":
        server.status = "stopped"
    elif action == "apply":
        try:
            agent_result = await apply_dns_config(db, server.instance_id)
            server.status = "running"
            await db.commit()
        except AgentClientError as exc:
            server.status = "error"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to apply DNS config on agent: {exc}",
            ) from exc
    elif action == "reload":
        try:
            agent_result = await reload_dns_agent(db, server.instance_id)
        except AgentClientError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reload BIND on agent: {exc}",
            ) from exc

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="deploy",
        resource_type="dns_server",
        resource_id=server.id,
        instance_id=server.instance_id,
        new_value={"operation": action, "agent_result": agent_result},
    )
    return {"status": "success", "action": action, "server_id": server_id, "agent_result": agent_result}


@router.get("/servers/{server_id}/zones", response_model=List[DNSZoneResponse])
async def list_zones(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSZone).where(DNSZone.server_id == server_id).order_by(DNSZone.id)
    )
    zones = result.scalars().all()

    responses: List[DNSZoneResponse] = []
    for zone in zones:
        count_result = await db.execute(
            select(func.count(DNSRecord.id)).where(DNSRecord.zone_id == zone.id)
        )
        item = DNSZoneResponse.model_validate(zone)
        item.records_count = int(count_result.scalar() or 0)
        responses.append(item)
    return responses


@router.post(
    "/servers/{server_id}/zones",
    response_model=DNSZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    server_id: int,
    data: DNSZoneCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    server_result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")

    zone = DNSZone(
        server_id=server_id,
        name=data.name.rstrip("."),
        description=data.description,
        zone_type=data.zone_type.value,
        is_reverse=data.is_reverse,
        reverse_network=data.reverse_network,
        serial=_serial_from_now(),
        refresh=data.refresh,
        retry=data.retry,
        expire=data.expire,
        minimum_ttl=data.minimum_ttl,
        dnssec_enabled=data.dnssec_enabled,
        enabled=data.enabled,
        created_by=user_id,
    )
    db.add(zone)
    await db.flush()

    if zone.zone_type in {DNSZoneType.MASTER.value, DNSZoneType.SLAVE.value}:
        ns_record = DNSRecord(
            zone_id=zone.id,
            name="@",
            record_type=DNSRecordType.NS.value,
            content=_ensure_fqdn(server.name),
            ttl=zone.minimum_ttl,
            is_system=True,
            created_by=user_id,
        )
        db.add(ns_record)

    await db.commit()
    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dns_zone",
        resource_id=zone.id,
        instance_id=server.instance_id,
    )
    await db.refresh(zone)
    _schedule_apply(background_tasks, server.instance_id)
    response = DNSZoneResponse.model_validate(zone)
    response.records_count = 1 if zone.zone_type in {DNSZoneType.MASTER.value, DNSZoneType.SLAVE.value} else 0
    return response


@router.post(
    "/servers/{server_id}/zones/reverse",
    response_model=DNSZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reverse_zone(
    server_id: int,
    data: CreateReverseZoneRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    zone_name = _reverse_zone_name(data.network)
    payload = DNSZoneCreate(
        name=zone_name,
        zone_type=DNSZoneType.MASTER,
        is_reverse=True,
        reverse_network=data.network,
        enabled=True,
    )
    created = await create_zone(server_id, payload, background_tasks, user_id, db)

    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == created.id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reverse zone not found")

    soa = DNSRecord(
        zone_id=zone.id,
        name="@",
        record_type=DNSRecordType.SOA.value,
        content=(
            f"{_ensure_fqdn(data.nameserver)} "
            f"{_ensure_fqdn(data.admin_email.replace('@', '.'))} "
            f"{zone.serial} {zone.refresh} {zone.retry} {zone.expire} {zone.minimum_ttl}"
        ),
        ttl=zone.minimum_ttl,
        is_system=True,
        created_by=user_id,
    )
    db.add(soa)
    await db.commit()

    count_result = await db.execute(
        select(func.count(DNSRecord.id)).where(DNSRecord.zone_id == zone.id)
    )
    response = DNSZoneResponse.model_validate(zone)
    response.records_count = int(count_result.scalar() or 0)
    return response


@router.get("/zones/detail/{zone_id}", response_model=DNSZoneResponse)
async def get_zone(
    zone_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")
    count_result = await db.execute(
        select(func.count(DNSRecord.id)).where(DNSRecord.zone_id == zone.id)
    )
    response = DNSZoneResponse.model_validate(zone)
    response.records_count = int(count_result.scalar() or 0)
    return response


@router.patch("/zones/{zone_id}", response_model=DNSZoneResponse)
async def update_zone(
    zone_id: int,
    data: DNSZoneUpdate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    zone.serial = _serial_from_now()

    await db.commit()
    instance_id = await _zone_instance_id(db, zone_id)
    _schedule_apply(background_tasks, instance_id)
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dns_zone",
        resource_id=zone.id,
        instance_id=None,
    )
    await db.refresh(zone)
    return DNSZoneResponse.model_validate(zone)


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")
    instance_id = await _zone_instance_id(db, zone_id)
    await db.delete(zone)
    await db.commit()
    _schedule_apply(background_tasks, instance_id)
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dns_zone",
        resource_id=zone_id,
        instance_id=None,
    )


@router.post("/zones/{zone_id}/sign")
async def sign_zone(
    zone_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")
    zone.dnssec_enabled = True

    existing_keys_result = await db.execute(
        select(DNSSECKey).where(DNSSECKey.zone_id == zone.id, DNSSECKey.is_active == True)
    )
    for key in existing_keys_result.scalars().all():
        key.is_active = False
        key.rotated_at = datetime.utcnow()

    ksk_tag = _new_key_tag(zone.name, "KSK", zone.dnssec_ksk_size)
    zsk_tag = _new_key_tag(zone.name, "ZSK", zone.dnssec_zsk_size)

    ksk_dnskey = _dnskey_line(zone.name, ksk_tag, zone.dnssec_algorithm)
    zsk_dnskey = _dnskey_line(zone.name, zsk_tag, zone.dnssec_algorithm)
    ds = _ds_line(zone.name, ksk_tag, ksk_dnskey)

    ksk = DNSSECKey(
        zone_id=zone.id,
        key_type="KSK",
        algorithm=zone.dnssec_algorithm,
        key_size=zone.dnssec_ksk_size,
        key_tag=ksk_tag,
        public_dnskey=ksk_dnskey,
        ds_record=ds,
        is_active=True,
        activated_at=datetime.utcnow(),
    )
    zsk = DNSSECKey(
        zone_id=zone.id,
        key_type="ZSK",
        algorithm=zone.dnssec_algorithm,
        key_size=zone.dnssec_zsk_size,
        key_tag=zsk_tag,
        public_dnskey=zsk_dnskey,
        is_active=True,
        activated_at=datetime.utcnow(),
    )
    db.add(ksk)
    db.add(zsk)

    zone.dnssec_ds_record = ds
    zone.serial = _serial_from_now()
    await db.commit()
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))
    await log_audit(
        db=db,
        user_id=user_id,
        action="deploy",
        resource_type="dns_zone_dnssec",
        resource_id=zone.id,
        instance_id=None,
        new_value={"dnssec_enabled": True, "ksk_tag": ksk_tag, "zsk_tag": zsk_tag},
    )
    return {"status": "success", "zone_id": zone_id, "dnssec_enabled": True}


@router.post("/zones/{zone_id}/unsign")
async def unsign_zone(
    zone_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")
    zone.dnssec_enabled = False
    zone.dnssec_ds_record = None
    existing_keys_result = await db.execute(
        select(DNSSECKey).where(DNSSECKey.zone_id == zone.id, DNSSECKey.is_active == True)
    )
    for key in existing_keys_result.scalars().all():
        key.is_active = False
        key.rotated_at = datetime.utcnow()
    zone.serial = _serial_from_now()
    await db.commit()
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))
    await log_audit(
        db=db,
        user_id=user_id,
        action="deploy",
        resource_type="dns_zone_dnssec",
        resource_id=zone.id,
        instance_id=None,
        new_value={"dnssec_enabled": False},
    )
    return {"status": "success", "zone_id": zone_id, "dnssec_enabled": False}


@router.get("/zones/{zone_id}/dnssec-keys", response_model=List[DNSSECKeyResponse])
async def list_dnssec_keys(
    zone_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSSECKey).where(DNSSECKey.zone_id == zone_id).order_by(DNSSECKey.id.desc())
    )
    return [DNSSECKeyResponse.model_validate(item) for item in result.scalars().all()]


@router.post("/zones/{zone_id}/dnssec-rollover", response_model=DNSSECKeyResponse)
async def dnssec_rollover(
    zone_id: int,
    data: DNSSECRolloverRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")

    key_type = data.key_type.upper()
    if key_type not in {"KSK", "ZSK"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid key type")

    current_active = await db.execute(
        select(DNSSECKey).where(
            DNSSECKey.zone_id == zone_id,
            DNSSECKey.key_type == key_type,
            DNSSECKey.is_active == True,
        )
    )
    for item in current_active.scalars().all():
        item.is_active = False
        item.rotated_at = datetime.utcnow()

    key_tag = _new_key_tag(zone.name, key_type, data.key_size)
    dnskey = _dnskey_line(zone.name, key_tag, data.algorithm)
    ds = _ds_line(zone.name, key_tag, dnskey) if key_type == "KSK" else None

    key = DNSSECKey(
        zone_id=zone.id,
        key_type=key_type,
        algorithm=data.algorithm,
        key_size=data.key_size,
        key_tag=key_tag,
        public_dnskey=dnskey,
        ds_record=ds,
        is_active=True,
        activated_at=datetime.utcnow(),
    )
    db.add(key)

    if key_type == "KSK":
        zone.dnssec_ds_record = ds

    zone.dnssec_enabled = True
    zone.serial = _serial_from_now()
    await db.commit()
    await db.refresh(key)
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))

    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dns_zone_dnssec_rollover",
        resource_id=zone.id,
        instance_id=None,
        new_value={"key_type": key_type, "key_tag": key_tag},
    )
    return DNSSECKeyResponse.model_validate(key)


@router.get("/zones/{zone_id}/records", response_model=List[DNSRecordResponse])
async def list_records(
    zone_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSRecord).where(DNSRecord.zone_id == zone_id).order_by(DNSRecord.id)
    )
    return [DNSRecordResponse.model_validate(record) for record in result.scalars().all()]


@router.post("/zones/{zone_id}/records", response_model=DNSRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    zone_id: int,
    data: DNSRecordCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")

    record = DNSRecord(
        zone_id=zone_id,
        name=data.name,
        record_type=data.record_type.value,
        content=data.content,
        ttl=data.ttl,
        priority=data.priority,
        weight=data.weight,
        port=data.port,
        flags=data.flags,
        tag=data.tag,
        comment=data.comment,
        created_by=user_id,
    )
    db.add(record)
    zone.serial = _serial_from_now()
    await db.commit()
    await db.refresh(record)
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))
    return DNSRecordResponse.model_validate(record)


@router.post("/zones/{zone_id}/records/bulk", response_model=List[DNSRecordResponse])
async def bulk_import_records(
    zone_id: int,
    data: BulkRecordImport,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")

    records: List[DNSRecord] = []
    for item in data.records:
        record = DNSRecord(
            zone_id=zone_id,
            name=item.name,
            record_type=item.record_type.value,
            content=item.content,
            ttl=item.ttl,
            priority=item.priority,
            weight=item.weight,
            port=item.port,
            flags=item.flags,
            tag=item.tag,
            comment=item.comment,
            created_by=user_id,
        )
        db.add(record)
        records.append(record)

    zone.serial = _serial_from_now()
    await db.commit()
    for record in records:
        await db.refresh(record)
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))
    return [DNSRecordResponse.model_validate(record) for record in records]


@router.post("/zones/{zone_id}/records/ptr", response_model=DNSRecordResponse)
async def create_ptr_record(
    zone_id: int,
    data: CreatePTRRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == zone_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS zone not found")
    if not zone.is_reverse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PTR records can only be created in reverse zones",
        )

    if zone.reverse_network:
        if ipaddress.ip_address(data.ip_address) not in ipaddress.ip_network(
            zone.reverse_network, strict=False
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP address is outside reverse zone network",
            )

    record = DNSRecord(
        zone_id=zone_id,
        name=_ptr_name_for_zone(data.ip_address, zone.name),
        record_type=DNSRecordType.PTR.value,
        content=_ensure_fqdn(data.hostname),
        ttl=data.ttl,
        created_by=user_id,
    )
    db.add(record)
    zone.serial = _serial_from_now()
    await db.commit()
    await db.refresh(record)
    _schedule_apply(background_tasks, await _zone_instance_id(db, zone_id))
    return DNSRecordResponse.model_validate(record)


@router.patch("/records/{record_id}", response_model=DNSRecordResponse)
async def update_record(
    record_id: int,
    data: DNSRecordUpdate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    record_result = await db.execute(select(DNSRecord).where(DNSRecord.id == record_id))
    record = record_result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS record not found")
    if record.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System DNS records cannot be modified",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "record_type" and value is not None:
            setattr(record, field, value.value)
        else:
            setattr(record, field, value)

    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == record.zone_id))
    zone = zone_result.scalar_one_or_none()
    if zone:
        zone.serial = _serial_from_now()
    await db.commit()
    await db.refresh(record)
    _schedule_apply(background_tasks, await _record_instance_id(db, record))
    return DNSRecordResponse.model_validate(record)


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    record_result = await db.execute(select(DNSRecord).where(DNSRecord.id == record_id))
    record = record_result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS record not found")
    if record.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System DNS records cannot be deleted",
        )

    zone_result = await db.execute(select(DNSZone).where(DNSZone.id == record.zone_id))
    zone = zone_result.scalar_one_or_none()
    instance_id = await _record_instance_id(db, record)
    await db.delete(record)
    if zone:
        zone.serial = _serial_from_now()
    await db.commit()
    _schedule_apply(background_tasks, instance_id)


@router.get("/zones/{zone_id}/slaves", response_model=List[DNSZoneSlaveResponse])
async def list_zone_slaves(
    zone_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSZoneSlave).where(DNSZoneSlave.zone_id == zone_id).order_by(DNSZoneSlave.id)
    )
    return [DNSZoneSlaveResponse.model_validate(item) for item in result.scalars().all()]


@router.get("/servers/{server_id}/tsig-keys", response_model=List[DNSTSIGKeyResponse])
async def list_tsig_keys(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    _ = user_id
    result = await db.execute(
        select(DNSTSIGKey).where(DNSTSIGKey.server_id == server_id).order_by(DNSTSIGKey.id)
    )
    return [DNSTSIGKeyResponse.model_validate(item) for item in result.scalars().all()]


@router.post(
    "/servers/{server_id}/tsig-keys",
    response_model=DNSTSIGKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tsig_key(
    server_id: int,
    data: DNSTSIGKeyCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    server_result = await db.execute(select(DNSServer).where(DNSServer.id == server_id))
    server = server_result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DNS server not found")

    key = DNSTSIGKey(
        server_id=server_id,
        name=data.name,
        algorithm=data.algorithm.value,
        secret=data.secret or _generate_tsig_secret(data.algorithm.value),
        is_active=data.is_active,
        created_by=user_id,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)
    _schedule_apply(background_tasks, server.instance_id)

    await log_audit(
        db=db,
        user_id=user_id,
        action="create",
        resource_type="dns_tsig_key",
        resource_id=key.id,
        instance_id=server.instance_id,
    )
    return DNSTSIGKeyResponse.model_validate(key)


@router.post("/tsig-keys/{key_id}/rotate", response_model=DNSTSIGKeyResponse)
async def rotate_tsig_key(
    key_id: int,
    data: DNSTSIGKeyRotate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    key_result = await db.execute(select(DNSTSIGKey).where(DNSTSIGKey.id == key_id))
    key = key_result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TSIG key not found")

    key.algorithm = data.algorithm.value
    key.secret = _generate_tsig_secret(data.algorithm.value)
    key.rotated_at = datetime.utcnow()
    key.is_active = True
    await db.commit()
    await db.refresh(key)
    _schedule_apply(background_tasks, await _server_instance_id(db, key.server_id))

    server_result = await db.execute(select(DNSServer).where(DNSServer.id == key.server_id))
    server = server_result.scalar_one_or_none()
    await log_audit(
        db=db,
        user_id=user_id,
        action="update",
        resource_type="dns_tsig_key",
        resource_id=key.id,
        instance_id=server.instance_id if server else None,
        new_value={"rotated": True, "algorithm": key.algorithm},
    )
    return DNSTSIGKeyResponse.model_validate(key)


@router.delete("/tsig-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tsig_key(
    key_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    key_result = await db.execute(select(DNSTSIGKey).where(DNSTSIGKey.id == key_id))
    key = key_result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TSIG key not found")

    key.is_active = False
    key.rotated_at = datetime.utcnow()
    await db.commit()
    _schedule_apply(background_tasks, await _server_instance_id(db, key.server_id))

    server_result = await db.execute(select(DNSServer).where(DNSServer.id == key.server_id))
    server = server_result.scalar_one_or_none()
    await log_audit(
        db=db,
        user_id=user_id,
        action="delete",
        resource_type="dns_tsig_key",
        resource_id=key.id,
        instance_id=server.instance_id if server else None,
    )
