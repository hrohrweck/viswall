"""
Viswall VPN Service Agent

Manages multiple VPN protocols on viswall instances:
- WireGuard (modern, recommended)
- IPsec/IKEv2 (strongSwan)
- OpenVPN
- L2TP/IPsec
- PPTP (legacy, not recommended)
"""

import asyncio
import subprocess
import json
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class VPNProtocol(Enum):
    WIREGUARD = "wireguard"
    IPSEC = "ipsec"
    OPENVPN = "openvpn"
    L2TP = "l2tp"
    PPTP = "pptp"

@dataclass
class VPNClientConfig:
    id: int
    name: str
    public_key: Optional[str]
    allowed_ips: str
    persistent_keepalive: int = 25

class WireGuardManager:
    """Manages WireGuard VPN interfaces and peers"""
    
    INTERFACE_PREFIX = "wg"
    
    def __init__(self, interface_name: str = "wg0"):
        self.interface_name = interface_name
        self.config_path = f"/etc/wireguard/{interface_name}.conf"
    
    async def generate_keypair(self) -> tuple[str, str]:
        """Generate WireGuard private and public key"""
        # Generate private key
        priv_proc = await asyncio.create_subprocess_exec(
            "wg", "genkey",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        private_key, _ = await priv_proc.communicate()
        private_key = private_key.decode().strip()
        
        # Generate public key
        pub_proc = await asyncio.create_subprocess_exec(
            "wg", "pubkey",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        public_key, _ = await pub_proc.communicate(private_key.encode())
        public_key = public_key.decode().strip()
        
        return private_key, public_key
    
    async def generate_preshared_key(self) -> str:
        """Generate preshared key for extra security"""
        proc = await asyncio.create_subprocess_exec(
            "wg", "genpsk",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        psk, _ = await proc.communicate()
        return psk.decode().strip()
    
    def create_server_config(
        self,
        private_key: str,
        listen_port: int = 51820,
        network_cidr: str = "10.200.0.0/24",
        ipv6_tunnel_network: Optional[str] = None,
        ipv6_nat_enabled: bool = False,
        post_up: Optional[str] = None,
        post_down: Optional[str] = None
    ) -> str:
        """Create WireGuard server configuration (dual-stack aware)"""
        addresses = [self._get_server_ip(network_cidr)]
        if ipv6_tunnel_network:
            addresses.append(self._get_server_ip(ipv6_tunnel_network))

        config = f"""[Interface]
PrivateKey = {private_key}
Address = {', '.join(addresses)}
ListenPort = {listen_port}
"""

        # Build PostUp/PostDown for dual-stack
        if not post_up:
            post_up_cmds = [
                f"iptables -A FORWARD -i {self.interface_name} -j ACCEPT",
                f"iptables -A FORWARD -o {self.interface_name} -j ACCEPT",
                f"iptables -t nat -A POSTROUTING -s {network_cidr} -o eth0 -j MASQUERADE",
            ]
            # IPv6 forwarding
            post_up_cmds.extend([
                f"ip6tables -A FORWARD -i {self.interface_name} -j ACCEPT",
                f"ip6tables -A FORWARD -o {self.interface_name} -j ACCEPT",
            ])
            if ipv6_tunnel_network and ipv6_nat_enabled:
                post_up_cmds.append(
                    f"ip6tables -t nat -A POSTROUTING -s {ipv6_tunnel_network} -o eth0 -j MASQUERADE"
                )
            post_up = "; ".join(post_up_cmds)

        if not post_down:
            post_down_cmds = [
                f"iptables -D FORWARD -i {self.interface_name} -j ACCEPT",
                f"iptables -D FORWARD -o {self.interface_name} -j ACCEPT",
                f"iptables -t nat -D POSTROUTING -s {network_cidr} -o eth0 -j MASQUERADE",
            ]
            post_down_cmds.extend([
                f"ip6tables -D FORWARD -i {self.interface_name} -j ACCEPT",
                f"ip6tables -D FORWARD -o {self.interface_name} -j ACCEPT",
            ])
            if ipv6_tunnel_network and ipv6_nat_enabled:
                post_down_cmds.append(
                    f"ip6tables -t nat -D POSTROUTING -s {ipv6_tunnel_network} -o eth0 -j MASQUERADE"
                )
            post_down = "; ".join(post_down_cmds)

        config += f"PostUp = {post_up}\n"
        config += f"PostDown = {post_down}\n"

        return config
    
    def add_peer(
        self,
        config: str,
        client: VPNClientConfig,
        preshared_key: Optional[str] = None
    ) -> str:
        """Add a peer to the WireGuard configuration"""
        peer_config = f"""
[Peer]
# {client.name} (ID: {client.id})
PublicKey = {client.public_key}
AllowedIPs = {client.allowed_ips}
PersistentKeepalive = {client.persistent_keepalive}
"""
        if preshared_key:
            peer_config += f"PresharedKey = {preshared_key}\n"
        
        return config + peer_config
    
    async def apply_config(self, config: str) -> bool:
        """Apply WireGuard configuration and start interface"""
        try:
            # Write config
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                f.write(config)
            os.chmod(self.config_path, 0o600)
            
            # Stop existing interface
            await self.stop()
            
            # Start interface
            proc = await asyncio.create_subprocess_exec(
                "wg-quick", "up", self.interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                print(f"WireGuard error: {stderr.decode()}")
                return False
            
            # Enable on boot
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "enable", f"wg-quick@{self.interface_name}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply WireGuard config: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop WireGuard interface"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "wg-quick", "down", self.interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return True
        except:
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get WireGuard interface status"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "wg", "show", self.interface_name, "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return json.loads(stdout.decode())
        except:
            return {}
    
    def _get_server_ip(self, cidr: str) -> str:
        """Get first usable IP from CIDR for server"""
        import ipaddress
        network = ipaddress.ip_network(cidr)
        return str(list(network.hosts())[0]) + f"/{network.prefixlen}"
    
    def create_client_config(
        self,
        client_private_key: str,
        client_ip: str,
        server_public_key: str,
        server_endpoint: str,
        allowed_ips: str = "0.0.0.0/0, ::/0",
        dns_servers: List[str] = None,
        persistent_keepalive: int = 25
    ) -> str:
        """Create client configuration file"""
        config = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}
"""
        if dns_servers:
            config += f"DNS = {', '.join(dns_servers)}\n"
        
        config += f"""
[Peer]
PublicKey = {server_public_key}
AllowedIPs = {allowed_ips}
Endpoint = {server_endpoint}
PersistentKeepalive = {persistent_keepalive}
"""
        return config


class IPSecManager:
    """Manages IPsec/IKEv2 VPN using strongSwan"""
    
    CONFIG_PATH = "/etc/ipsec.conf"
    SECRETS_PATH = "/etc/ipsec.secrets"
    
    async def generate_certificate(self, cn: str) -> tuple[str, str, str]:
        """Generate CA and server certificates"""
        # This would use ipsec pki commands
        # Simplified for structure
        return ("ca_cert", "server_cert", "server_key")
    
    def create_road_warrior_config(
        self,
        server_id: str,
        left_subnet: str,
        right_source_ip: str = "10.201.0.0/24",
        right_source_ip_v6: Optional[str] = None,
        eap_enabled: bool = True
    ) -> str:
        """Create IKEv2 road warrior (remote access) config (dual-stack aware)"""
        config = f"""config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2, mgr 2"
    uniqueids=yes
    strictcrlpolicy=no

conn {server_id}
    auto=add
    compress=no
    type=tunnel
    keyexchange=ikev2
    fragmentation=yes
    forceencaps=yes

    # Left (local) side
    left=%any
    leftid=@{server_id}
    leftcert=serverCert.pem
    leftsendcert=always
    leftsubnet={left_subnet}

    # Right (remote) side
    right=%any
    rightid=%any
    rightauth=eap-mschapv2
    rightsourceip={right_source_ip}
    rightdns=1.1.1.1,1.0.0.1

    # IKE (Phase 1) - Modern secure defaults
    ike=aes256gcm16-sha384-ecp384!
    esp=aes256gcm16-sha384-ecp384!

    # DPD
    dpdaction=clear
    dpddelay=300s
    dpdtimeout=1500s

    # Lifetime
    ikelifetime=24h
    lifetime=8h
"""
        if right_source_ip_v6:
            config += f"    rightsourceip={right_source_ip_v6}\n"
        return config
    
    def create_site_to_site_config(
        self,
        conn_name: str,
        local_subnet: str,
        remote_gateway: str,
        remote_subnet: str,
        auth_method: str = "psk"
    ) -> str:
        """Create site-to-site IPsec config"""
        config = f"""conn {conn_name}
    auto=start
    type=tunnel
    keyexchange=ikev2
    
    left=%defaultroute
    leftsubnet={local_subnet}
    
    right={remote_gateway}
    rightsubnet={remote_subnet}
    
    ike=aes256-sha256-modp2048!
    esp=aes256-sha256!
    
    dpddelay=30
    dpdtimeout=120
    dpdaction=restart
"""
        if auth_method == "psk":
            config += "    authby=secret\n"
        else:
            config += "    leftcert=serverCert.pem\n    rightcert=remoteCert.pem\n"
        
        return config
    
    async def apply_config(self, config: str, secrets: str) -> bool:
        """Apply IPsec configuration"""
        try:
            with open(self.CONFIG_PATH, 'w') as f:
                f.write(config)
            
            with open(self.SECRETS_PATH, 'w') as f:
                f.write(secrets)
            os.chmod(self.SECRETS_PATH, 0o600)
            
            # Reload strongSwan
            proc = await asyncio.create_subprocess_exec(
                "ipsec", "restart",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            return proc.returncode == 0
        except Exception as e:
            print(f"IPsec config error: {e}")
            return False


class OpenVPNManager:
    """Manages OpenVPN server"""
    
    CONFIG_PATH = "/etc/openvpn/server.conf"
    EASYRSA_PATH = "/etc/openvpn/easy-rsa"
    
    def create_server_config(
        self,
        port: int = 1194,
        protocol: str = "udp",
        network: str = "10.202.0.0",
        netmask: str = "255.255.255.0",
        ipv6_tunnel_network: Optional[str] = None,
        cipher: str = "AES-256-GCM",
        auth_digest: str = "SHA256",
        tls_version: str = "1.2"
    ) -> str:
        """Create OpenVPN server configuration (dual-stack aware)"""
        config = f"""# OpenVPN Server Configuration
port {port}
proto {protocol}
dev tun

# Network
server {network} {netmask}
ifconfig-pool-persist /var/log/openvpn/ipp.txt
"""
        if ipv6_tunnel_network:
            config += f"server-ipv6 {ipv6_tunnel_network}\n"

        config += """
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 1.0.0.1"

# Crypto
cipher {cipher}
auth {auth_digest}
tls-version-min {tls_version}
tls-cipher TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384:TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384

# Hardening
user nobody
group nogroup
persist-key
persist-tun

# Logging
status /var/log/openvpn/openvpn-status.log
verb 3

# Certificates
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
crl-verify /etc/openvpn/crl.pem

# TLS Auth
tls-auth /etc/openvpn/ta.key 0

# Connection settings
keepalive 10 120
max-clients 1000

# Do not use compression (VORACLE attack)
;compress lz4-v2

# Client configs
client-config-dir /etc/openvpn/ccd
"""
        return config
    
    async def generate_client_certificate(self, client_name: str) -> tuple[str, str]:
        """Generate client certificate and key"""
        # Would use easy-rsa
        # ./easyrsa build-client-full client1 nopass
        return (f"{client_name}.crt", f"{client_name}.key")
    
    def create_client_config(
        self,
        client_name: str,
        server_endpoint: str,
        ca_cert: str,
        client_cert: str,
        client_key: str,
        tls_auth_key: str
    ) -> str:
        """Create client .ovpn file"""
        config = f"""client
dev tun
proto udp
remote {server_endpoint} 1194
resolv-retry infinite
nobind
persist-key
persist-tun

cipher AES-256-GCM
auth SHA256
tls-version-min 1.2

verb 3

<ca>
{ca_cert}
</ca>

<cert>
{client_cert}
</cert>

<key>
{client_key}
</key>

<tls-auth>
{tls_auth_key}
</tls-auth>
key-direction 1
"""
        return config


class VPNAgent:
    """Main VPN agent that manages all protocols"""
    
    def __init__(self):
        self.wireguard = WireGuardManager()
        self.ipsec = IPSecManager()
        self.openvpn = OpenVPNManager()
    
    async def deploy_server(self, config: Dict[str, Any]) -> bool:
        """Deploy a VPN server based on configuration"""
        protocol = config.get("protocol")
        
        if protocol == "wireguard":
            return await self._deploy_wireguard(config)
        elif protocol == "ipsec":
            return await self._deploy_ipsec(config)
        elif protocol == "openvpn":
            return await self._deploy_openvpn(config)
        else:
            print(f"Unsupported protocol: {protocol}")
            return False
    
    async def _deploy_wireguard(self, config: Dict[str, Any]) -> bool:
        """Deploy WireGuard server"""
        # Generate or use provided keys
        private_key = config.get("private_key")
        if not private_key:
            private_key, public_key = await self.wireguard.generate_keypair()

        wg_cfg = config.get("wireguard_config", {})

        # Create server config
        wg_config = self.wireguard.create_server_config(
            private_key=private_key,
            listen_port=config.get("listen_port", 51820),
            network_cidr=config.get("network_cidr", "10.200.0.0/24"),
            ipv6_tunnel_network=config.get("ipv6_tunnel_network"),
            ipv6_nat_enabled=wg_cfg.get("ipv6_nat_enabled", False),
            post_up=config.get("post_up"),
            post_down=config.get("post_down")
        )

        # Add existing peers
        for peer in config.get("peers", []):
            client = VPNClientConfig(**peer)
            wg_config = self.wireguard.add_peer(wg_config, client)

        return await self.wireguard.apply_config(wg_config)
    
    async def _deploy_ipsec(self, config: Dict[str, Any]) -> bool:
        """Deploy IPsec server"""
        # Create configuration
        if config.get("mode") == "road_warrior":
            ipsec_config = self.ipsec.create_road_warrior_config(
                server_id=config.get("name", "viswall"),
                left_subnet=config.get("left_subnet", "0.0.0.0/0"),
                right_source_ip=config.get("network_cidr", "10.201.0.0/24"),
                right_source_ip_v6=config.get("ipv6_tunnel_network")
            )
        else:
            ipsec_config = self.ipsec.create_site_to_site_config(**config)

        secrets = config.get("secrets", "")
        return await self.ipsec.apply_config(ipsec_config, secrets)
    
    async def _deploy_openvpn(self, config: Dict[str, Any]) -> bool:
        """Deploy OpenVPN server"""
        ovpn_config = self.openvpn.create_server_config(
            port=config.get("port", 1194),
            protocol=config.get("protocol", "udp"),
            network=config.get("network", "10.202.0.0"),
            ipv6_tunnel_network=config.get("ipv6_tunnel_network"),
            cipher=config.get("cipher", "AES-256-GCM")
        )
        
        # Write and start
        try:
            with open(self.openvpn.CONFIG_PATH, 'w') as f:
                f.write(ovpn_config)
            
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "restart", "openvpn@server",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            print(f"OpenVPN deploy error: {e}")
            return False


def create_app(agent: VPNAgent):
    from fastapi import FastAPI, HTTPException

    app = FastAPI(title="Viswall VPN Agent", version="1.0.0")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "vpn-agent"}

    @app.post("/deploy")
    async def deploy(config: dict):
        try:
            await agent.deploy_server(config)
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/start")
    async def start(protocol: str):
        try:
            if protocol == "wireguard":
                await agent.wg.start()
            elif protocol == "ipsec":
                await agent.ipsec.start()
            elif protocol == "openvpn":
                await agent.ovpn.start()
            else:
                raise HTTPException(status_code=400, detail=f"Unknown protocol: {protocol}")
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/stop")
    async def stop(protocol: str):
        try:
            if protocol == "wireguard":
                await agent.wg.stop()
            elif protocol == "ipsec":
                await agent.ipsec.stop()
            elif protocol == "openvpn":
                await agent.ovpn.stop()
            else:
                raise HTTPException(status_code=400, detail=f"Unknown protocol: {protocol}")
            return {"success": True}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/client")
    async def create_client(data: dict):
        try:
            config = await agent.create_client_config(data)
            return {"success": True, "config": config}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


async def main():
    """VPN Agent main loop"""
    agent = VPNAgent()

    print("Viswall VPN Agent started")
    print("Supported protocols: WireGuard, IPsec/IKEv2, OpenVPN")

    app = create_app(agent)
    import uvicorn
    config_uvicorn = uvicorn.Config(app, host="::", port=8083, loop="asyncio")
    server = uvicorn.Server(config_uvicorn)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
