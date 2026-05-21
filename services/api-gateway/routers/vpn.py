from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
import json

from shared.database import get_db
from shared.models import (
    VPNServer,
    VPNClient,
    VPNConnection,
    VPNRoute,
    Instance,
)
from shared.schemas import (
    VPNServerCreate,
    VPNServerUpdate,
    VPNServerResponse,
    VPNServerStats,
    VPNClientCreate,
    VPNClientUpdate,
    VPNClientResponse,
    VPNClientConfig,
    VPNConnectionResponse,
    VPNRouteCreate,
    VPNRouteResponse,
    VPNBulkGenerateRequest,
    VPNBulkGenerateResponse,
    VPNProtocolRecommendation,
    VPNProtocol,
    VPNStatus,
    VPNClientType,
    VPNAuthType,
)
from shared.security import require_auth, require_admin
from shared.audit_logger import log_audit
from utils.agent_client import agent_request, AgentClientError

router = APIRouter()


# ============================================================================
# Protocol recommendations endpoint
# ============================================================================

@router.get("/protocols/recommendations", response_model=List[VPNProtocolRecommendation])
async def get_protocol_recommendations():
    """Get VPN protocol recommendations with security/performance scores"""
    return [
        VPNProtocolRecommendation(
            protocol=VPNProtocol.WIREGUARD,
            priority=1,
            security_score=95,
            performance_score=98,
            compatibility_score=75,
            description="Modern, fast, simple VPN protocol. Uses state-of-the-art cryptography (Curve25519, ChaCha20, Poly1305).",
            use_cases=["Road warriors", "Site-to-site", "Containers", "Mobile devices"]
        ),
        VPNProtocolRecommendation(
            protocol=VPNProtocol.IPSEC,
            priority=2,
            security_score=90,
            performance_score=85,
            compatibility_score=90,
            description="Enterprise standard. IKEv2 with modern crypto (AES-GCM, ECDH) provides excellent security.",
            use_cases=["Enterprise deployments", "Native OS support", "Site-to-site", "Mobile devices"]
        ),
        VPNProtocolRecommendation(
            protocol=VPNProtocol.OPENVPN,
            priority=3,
            security_score=88,
            performance_score=75,
            compatibility_score=95,
            description="Well-tested, flexible, widely supported. Slower than WireGuard but very compatible.",
            use_cases=["Legacy support", "Complex routing", "Bridge mode", "Authentication flexibility"]
        ),
        VPNProtocolRecommendation(
            protocol=VPNProtocol.L2TP,
            priority=4,
            security_score=60,
            performance_score=70,
            compatibility_score=98,
            description="Widely supported legacy protocol. Requires IPsec for security. Acceptable for compatibility only.",
            use_cases=["Legacy clients", "No custom software", "Mobile compatibility"]
        ),
        VPNProtocolRecommendation(
            protocol=VPNProtocol.PPTP,
            priority=5,
            security_score=20,
            performance_score=80,
            compatibility_score=100,
            description="DEPRECATED - Insecure protocol. Only for legacy compatibility. NOT RECOMMENDED.",
            use_cases=["Legacy systems only", "Last resort compatibility"]
        )
    ]


# ============================================================================
# Server endpoints
# ============================================================================

@router.get("/servers/{instance_id}", response_model=List[VPNServerResponse])
async def list_servers(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List all VPN servers for an instance"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.instance_id == instance_id)
    )
    servers = result.scalars().all()
    return [VPNServerResponse.model_validate(s) for s in servers]


@router.post("/servers/{instance_id}", response_model=VPNServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    instance_id: int,
    data: VPNServerCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new VPN server"""
    # Set default ports based on protocol
    port_mapping = {
        VPNProtocol.WIREGUARD: 51820,
        VPNProtocol.IPSEC: 500,
        VPNProtocol.OPENVPN: 1194,
        VPNProtocol.L2TP: 1701,
        VPNProtocol.PPTP: 1723,
    }

    listen_port = data.listen_port or port_mapping.get(data.protocol, 51820)

    # Build protocol-specific config
    config = {}
    if data.protocol == VPNProtocol.WIREGUARD and data.wireguard_config:
        config = data.wireguard_config.model_dump()
    elif data.protocol == VPNProtocol.IPSEC and data.ipsec_config:
        config = data.ipsec_config.model_dump()
    elif data.protocol == VPNProtocol.OPENVPN and data.openvpn_config:
        config = data.openvpn_config.model_dump()
    elif data.protocol == VPNProtocol.L2TP and data.l2tp_config:
        config = data.l2tp_config.model_dump()
    elif data.protocol == VPNProtocol.PPTP and data.pptp_config:
        config = data.pptp_config.model_dump()

    server = VPNServer(
        instance_id=instance_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        protocol=data.protocol.value,
        listen_address=data.listen_address,
        listen_port=listen_port,
        network_cidr=data.network_cidr,
        dns_servers=data.dns_servers,
        push_routes=data.push_routes,
        internet_redirect=data.internet_redirect,
        config=config,
        status=VPNStatus.STOPPED.value,
        connected_clients=0,
        bytes_received=0,
        bytes_sent=0,
        created_by=user_id,
    )

    db.add(server)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="create", resource_type="vpn_server", resource_id=server.id, instance_id=instance_id)

    await db.refresh(server)

    return VPNServerResponse.model_validate(server)


@router.get("/servers/detail/{server_id}", response_model=VPNServerResponse)
async def get_server(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get VPN server details"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    return VPNServerResponse.model_validate(server)


@router.patch("/servers/{server_id}", response_model=VPNServerResponse)
async def update_server(
    server_id: int,
    data: VPNServerUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update VPN server configuration"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="update", resource_type="vpn_server", resource_id=server.id, instance_id=server.instance_id)

    await db.refresh(server)

    return VPNServerResponse.model_validate(server)


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a VPN server and all its clients"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    await db.delete(server)
    await db.commit()
    # Audit log
    await log_audit(db=db, user_id=user_id, action="delete", resource_type="vpn_server", resource_id=server_id, instance_id=server.instance_id)



@router.post("/servers/{server_id}/start")
async def start_server(
    server_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Start the VPN server"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    try:
        await agent_request(
            db=db,
            instance_id=server.instance_id,
            method="POST",
            path="/start",
            json_data={"protocol": server.protocol},
        )
        server.status = VPNStatus.RUNNING.value
        await db.commit()
        return {"status": "success", "action": "start", "server_id": server_id}
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")


@router.post("/servers/{server_id}/stop")
async def stop_server(
    server_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stop the VPN server"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    try:
        await agent_request(
            db=db,
            instance_id=server.instance_id,
            method="POST",
            path="/stop",
            json_data={"protocol": server.protocol},
        )
        server.status = VPNStatus.STOPPED.value
        await db.commit()
        return {"status": "success", "action": "stop", "server_id": server_id}
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")


@router.post("/servers/{server_id}/restart")
async def restart_server(
    server_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Restart the VPN server"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    server.status = VPNStatus.RESTARTING.value
    await db.commit()

    try:
        await agent_request(
            db=db,
            instance_id=server.instance_id,
            method="POST",
            path="/stop",
            json_data={"protocol": server.protocol},
        )
        await agent_request(
            db=db,
            instance_id=server.instance_id,
            method="POST",
            path="/start",
            json_data={"protocol": server.protocol},
        )
        server.status = VPNStatus.RUNNING.value
        await db.commit()
        return {"status": "success", "action": "restart", "server_id": server_id}
    except AgentClientError as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e}")


@router.get("/servers/{server_id}/stats", response_model=VPNServerStats)
async def get_server_stats(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time VPN server statistics"""
    result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    # Get active connections
    conn_result = await db.execute(
        select(VPNConnection).where(
            and_(
                VPNConnection.server_id == server_id,
                VPNConnection.status == "active"
            )
        )
    )
    connections = conn_result.scalars().all()

    client_list = []
    for conn in connections:
        client_result = await db.execute(
            select(VPNClient).where(VPNClient.id == conn.client_id)
        )
        client = client_result.scalar_one_or_none()
        client_list.append({
            "client_id": conn.client_id,
            "client_name": client.name if client else "Unknown",
            "virtual_ip": conn.virtual_ip,
            "client_ip": conn.client_ip,
            "connected_at": conn.connected_at.isoformat() if conn.connected_at else None,
            "bytes_received": conn.bytes_received,
            "bytes_sent": conn.bytes_sent,
        })

    return VPNServerStats(
        server_id=server_id,
        status=VPNStatus(server.status),
        uptime_seconds=0,  # Would need tracking
        connected_clients=len(connections),
        total_bytes_received=server.bytes_received,
        total_bytes_sent=server.bytes_sent,
        client_list=client_list,
    )


# ============================================================================
# Client endpoints
# ============================================================================

@router.get("/servers/{server_id}/clients", response_model=List[VPNClientResponse])
async def list_clients(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List all clients for a VPN server"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.server_id == server_id)
    )
    clients = result.scalars().all()
    return [VPNClientResponse.model_validate(c) for c in clients]


@router.post("/servers/{server_id}/clients", response_model=VPNClientResponse)
async def create_client(
    server_id: int,
    data: VPNClientCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new VPN client"""
    # Verify server exists
    server_result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    # Generate keys based on protocol
    public_key = None
    config_file = None
    config_qr = None

    if server.protocol == VPNProtocol.WIREGUARD.value:
        # Generate a placeholder public key
        public_key = f"placeholder_{server_id}_{data.name.replace(' ', '_')}"

    # Build a basic config file
    config_data = _generate_client_config(server, data, public_key)
    config_file = base64.b64encode(config_data.encode()).decode()

    client = VPNClient(
        server_id=server_id,
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        client_type=data.client_type.value,
        auth_type=data.auth_type.value,
        public_key=public_key,
        assigned_ip=data.assigned_ip,
        allowed_ips=data.allowed_ips,
        push_routes_override=data.push_routes_override,
        user_id=data.user_id,
        config_file=config_file,
        config_qr=config_qr,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    return VPNClientResponse.model_validate(client)


@router.post("/servers/{server_id}/clients/bulk", response_model=VPNBulkGenerateResponse)
async def bulk_create_clients(
    server_id: int,
    data: VPNBulkGenerateRequest,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Bulk generate VPN clients (e.g., for an office)"""
    server_result = await db.execute(
        select(VPNServer).where(VPNServer.id == server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    clients = []
    for i in range(data.count):
        name = f"{data.name_prefix}_{i + 1}"
        public_key = f"placeholder_{server_id}_{name}"

        config_data = _generate_client_config(
            server,
            VPNClientCreate(name=name, auth_type=data.auth_type),
            public_key,
        )
        config_file = base64.b64encode(config_data.encode()).decode()

        client = VPNClient(
            server_id=server_id,
            name=name,
            enabled=True,
            client_type=VPNClientType.USER.value,
            auth_type=data.auth_type.value,
            public_key=public_key,
            config_file=config_file,
        )
        db.add(client)
        clients.append(client)

    await db.commit()

    # Refresh all clients to get IDs
    for client in clients:
        await db.refresh(client)

    return VPNBulkGenerateResponse(
        generated=len(clients),
        clients=[VPNClientResponse.model_validate(c) for c in clients],
        configs_zip="",  # Would generate a real zip
    )


@router.get("/clients/{client_id}", response_model=VPNClientResponse)
async def get_client(
    client_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get client details"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found"
        )

    return VPNClientResponse.model_validate(client)


@router.patch("/clients/{client_id}", response_model=VPNClientResponse)
async def update_client(
    client_id: int,
    data: VPNClientUpdate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update client configuration"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)

    return VPNClientResponse.model_validate(client)


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revoke and delete a client"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found"
        )

    await db.delete(client)
    await db.commit()


@router.get("/clients/{client_id}/config")
async def download_client_config(
    client_id: int,
    format: str = "auto",
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Download client configuration file"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found"
        )

    server_result = await db.execute(
        select(VPNServer).where(VPNServer.id == client.server_id)
    )
    server = server_result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN server not found"
        )

    # Determine config format
    config_format = format
    if config_format == "auto":
        if server.protocol == VPNProtocol.WIREGUARD.value:
            config_format = "wg-quick"
        elif server.protocol == VPNProtocol.OPENVPN.value:
            config_format = "ovpn"
        else:
            config_format = "txt"

    # Generate config
    config_data = _generate_client_config_for_download(server, client, config_format)
    filename = f"{client.name.replace(' ', '_')}.{config_format}"

    return VPNClientConfig(
        client_id=client_id,
        server_name=server.name,
        protocol=VPNProtocol(server.protocol),
        config_format=config_format,
        config_data=base64.b64encode(config_data.encode()).decode(),
        filename=filename,
    )


@router.post("/clients/{client_id}/regenerate")
async def regenerate_client_credentials(
    client_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate client keys/credentials (if compromised)"""
    result = await db.execute(
        select(VPNClient).where(VPNClient.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VPN client not found"
        )

    server_result = await db.execute(
        select(VPNServer).where(VPNServer.id == client.server_id)
    )
    server = server_result.scalar_one_or_none()

    # Generate new keys
    new_public_key = f"regenerated_{client_id}_{datetime.utcnow().timestamp()}"
    client.public_key = new_public_key

    # Regenerate config
    config_data = _generate_client_config_for_download(server, client, "txt")
    client.config_file = base64.b64encode(config_data.encode()).decode()

    await db.commit()

    return {"status": "success", "message": "Client credentials regenerated"}


# ============================================================================
# Connection tracking
# ============================================================================

@router.get("/servers/{server_id}/connections", response_model=List[VPNConnectionResponse])
async def list_connections(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List active connections for a server"""
    result = await db.execute(
        select(VPNConnection).where(
            and_(
                VPNConnection.server_id == server_id,
                VPNConnection.status == "active"
            )
        )
    )
    connections = result.scalars().all()

    response = []
    for conn in connections:
        client_result = await db.execute(
            select(VPNClient).where(VPNClient.id == conn.client_id)
        )
        client = client_result.scalar_one_or_none()

        response.append(
            VPNConnectionResponse(
                id=conn.id,
                server_id=conn.server_id,
                client_id=conn.client_id,
                client_name=client.name if client else "Unknown",
                protocol=VPNProtocol(conn.protocol) if conn.protocol else VPNProtocol.WIREGUARD,
                client_ip=conn.client_ip or "",
                virtual_ip=conn.virtual_ip or "",
                connected_at=conn.connected_at,
                bytes_received=conn.bytes_received,
                bytes_sent=conn.bytes_sent,
                status=conn.status,
            )
        )

    return response


@router.get("/servers/{server_id}/connections/history", response_model=List[VPNConnectionResponse])
async def list_connection_history(
    server_id: int,
    limit: int = 100,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List historical connections"""
    result = await db.execute(
        select(VPNConnection)
        .where(VPNConnection.server_id == server_id)
        .order_by(VPNConnection.connected_at.desc())
        .limit(limit)
    )
    connections = result.scalars().all()

    response = []
    for conn in connections:
        client_result = await db.execute(
            select(VPNClient).where(VPNClient.id == conn.client_id)
        )
        client = client_result.scalar_one_or_none()

        response.append(
            VPNConnectionResponse(
                id=conn.id,
                server_id=conn.server_id,
                client_id=conn.client_id,
                client_name=client.name if client else "Unknown",
                protocol=VPNProtocol(conn.protocol) if conn.protocol else VPNProtocol.WIREGUARD,
                client_ip=conn.client_ip or "",
                virtual_ip=conn.virtual_ip or "",
                connected_at=conn.connected_at,
                bytes_received=conn.bytes_received,
                bytes_sent=conn.bytes_sent,
                status=conn.status,
            )
        )

    return response


@router.post("/connections/{connection_id}/disconnect")
async def disconnect_client(
    connection_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Force disconnect a client"""
    result = await db.execute(
        select(VPNConnection).where(VPNConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    connection.status = "disconnected"
    connection.disconnected_at = datetime.utcnow()
    connection.disconnect_reason = "admin_disconnect"
    await db.commit()

    return {"status": "success", "message": "Client disconnected"}


# ============================================================================
# Routes (split tunneling)
# ============================================================================

@router.get("/servers/{server_id}/routes", response_model=List[VPNRouteResponse])
async def list_routes(
    server_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List VPN-specific routes (for split tunneling)"""
    result = await db.execute(
        select(VPNRoute)
        .where(VPNRoute.server_id == server_id)
        .order_by(VPNRoute.order_index)
    )
    routes = result.scalars().all()
    return [VPNRouteResponse.model_validate(r) for r in routes]


@router.post("/servers/{server_id}/routes", response_model=VPNRouteResponse)
async def create_route(
    server_id: int,
    data: VPNRouteCreate,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a route to the VPN configuration"""
    # Get next order index
    result = await db.execute(
        select(func.count(VPNRoute.id)).where(VPNRoute.server_id == server_id)
    )
    order_index = (result.scalar() or 0) * 10

    route = VPNRoute(
        server_id=server_id,
        destination=data.destination,
        gateway=data.gateway,
        metric=data.metric,
        apply_to_all=data.apply_to_all,
        specific_clients=data.specific_clients,
        description=data.description,
        order_index=order_index,
    )

    db.add(route)
    await db.commit()
    await db.refresh(route)

    return VPNRouteResponse.model_validate(route)


@router.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: int,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a VPN route"""
    result = await db.execute(
        select(VPNRoute).where(VPNRoute.id == route_id)
    )
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )

    await db.delete(route)
    await db.commit()


# ============================================================================
# Site-to-site VPN helpers
# ============================================================================

@router.post("/site-to-site/initialize")
async def initialize_site_to_site(
    local_instance_id: int,
    remote_endpoint: str,
    remote_public_key: str,
    protocol: VPNProtocol = VPNProtocol.WIREGUARD,
    user_id: int = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Initialize a site-to-site VPN tunnel"""
    # Check local instance exists
    result = await db.execute(
        select(Instance).where(Instance.id == local_instance_id)
    )
    instance = result.scalar_one_or_none()

    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Local instance not found"
        )

    # Create a site-to-site server if not exists
    server_name = f"site-to-site-{remote_endpoint.replace(':', '-')}"

    existing = await db.execute(
        select(VPNServer).where(
            and_(
                VPNServer.instance_id == local_instance_id,
                VPNServer.name == server_name,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Site-to-site tunnel already exists"
        )

    config = {
        "remote_endpoint": remote_endpoint,
        "remote_public_key": remote_public_key,
        "tunnel_type": "site-to-site",
    }

    if protocol == VPNProtocol.WIREGUARD:
        config["private_key"] = None
        config["listen_port"] = 51820

    server = VPNServer(
        instance_id=local_instance_id,
        name=server_name,
        description=f"Site-to-site tunnel to {remote_endpoint}",
        enabled=True,
        protocol=protocol.value,
        listen_address="0.0.0.0",
        listen_port=51820,
        network_cidr="10.255.0.0/30",
        config=config,
        status=VPNStatus.STOPPED.value,
        created_by=user_id,
    )

    db.add(server)
    await db.commit()
    await db.refresh(server)

    return {
        "status": "success",
        "server_id": server.id,
        "message": "Site-to-site tunnel initialized. Start the server to activate.",
    }


@router.get("/site-to-site/status")
async def get_site_to_site_status(
    instance_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get status of all site-to-site connections"""
    result = await db.execute(
        select(VPNServer).where(
            and_(
                VPNServer.instance_id == instance_id,
                VPNServer.name.like("site-to-site-%")
            )
        )
    )
    servers = result.scalars().all()

    return [
        {
            "server_id": s.id,
            "name": s.name,
            "status": s.status,
            "protocol": s.protocol,
            "remote_endpoint": s.config.get("remote_endpoint") if s.config else None,
        }
        for s in servers
    ]


# ============================================================================
# Helper functions
# ============================================================================

def _generate_client_config(
    server: VPNServer,
    data: VPNClientCreate,
    public_key: Optional[str],
) -> str:
    """Generate a basic client configuration text"""
    lines = [
        f"# VPN Client Configuration",
        f"# Server: {server.name}",
        f"# Protocol: {server.protocol}",
        f"# Client: {data.name}",
        f"",
    ]

    if server.protocol == VPNProtocol.WIREGUARD.value:
        lines.extend([
            "[Interface]",
            f"# PrivateKey = <generated>",
            f"Address = {data.assigned_ip or '10.200.0.x/24'}",
            f"DNS = {', '.join(server.dns_servers) if server.dns_servers else '1.1.1.1'}",
            f"",
            "[Peer]",
            f"PublicKey = {server.config.get('public_key', '<server-public-key>') if server.config else '<server-public-key>'}",
            f"Endpoint = {server.listen_address}:{server.listen_port}",
            f"AllowedIPs = {', '.join(data.allowed_ips) if data.allowed_ips else '0.0.0.0/0'}",
            f"PersistentKeepalive = 25",
        ])
    elif server.protocol == VPNProtocol.OPENVPN.value:
        lines.extend([
            "client",
            "dev tun",
            f"proto {server.config.get('protocol', 'udp') if server.config else 'udp'}",
            f"remote {server.listen_address} {server.listen_port}",
            "resolv-retry infinite",
            "nobind",
            "persist-key",
            "persist-tun",
            f"remote-cert-tls server",
            f"cipher {server.config.get('cipher', 'AES-256-GCM') if server.config else 'AES-256-GCM'}",
            f"verb 3",
        ])
    else:
        lines.extend([
            f"Protocol: {server.protocol}",
            f"Server: {server.listen_address}:{server.listen_port}",
            f"Network: {server.network_cidr}",
        ])

    return "\n".join(lines)


def _generate_client_config_for_download(
    server: VPNServer,
    client: VPNClient,
    config_format: str,
) -> str:
    """Generate client configuration for download"""
    data = VPNClientCreate(
        name=client.name,
        assigned_ip=client.assigned_ip,
        allowed_ips=client.allowed_ips or [],
    )
    return _generate_client_config(server, data, client.public_key)
