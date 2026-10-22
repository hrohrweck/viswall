"""Policy routing management for the Viswall firewall agent.

Ported from the former single-file agent
(``services/firewall-service/firewall_agent.py``, ``RoutingManager``) — moved,
not improved. Idempotent tagged policy routing is todo 13.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RoutingRule:
    id: int
    name: str
    source: Optional[str] = None
    destination: Optional[str] = None
    table: int = 254  # Main routing table
    gateway: Optional[str] = None
    interface: Optional[str] = None
    mark: Optional[int] = None  # fwmark for policy routing
    priority: int = 100


class RoutingManager:
    """Manages policy-based routing"""

    RT_TABLES_PATH = "/etc/iproute2/rt_tables"

    async def add_routing_table(self, name: str, number: int) -> bool:
        """Add custom routing table"""
        try:
            # Check if already exists
            with open(self.RT_TABLES_PATH, "r") as f:
                content = f.read()
                if name in content:
                    return True

            # Add table
            with open(self.RT_TABLES_PATH, "a") as f:
                f.write(f"{number} {name}\n")

            return True
        except Exception as e:
            print(f"Failed to add routing table: {e}")
            return False

    async def add_route(
        self,
        destination: str,
        gateway: Optional[str] = None,
        interface: Optional[str] = None,
        table: str = "main",
        source: Optional[str] = None,
        metric: Optional[int] = None,
    ) -> bool:
        """Add a route"""
        try:
            args = ["ip", "route", "add", destination]

            if gateway:
                args.extend(["via", gateway])
            if interface:
                args.extend(["dev", interface])
            if source:
                args.extend(["src", source])
            if metric:
                args.extend(["metric", str(metric)])

            args.extend(["table", table])

            proc = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0

        except Exception as e:
            print(f"Failed to add route: {e}")
            return False

    async def add_policy_rule(
        self,
        table: int,
        priority: int,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        mark: Optional[int] = None,
        interface: Optional[str] = None,
    ) -> bool:
        """Add policy routing rule"""
        try:
            args = ["ip", "rule", "add"]

            if source:
                args.extend(["from", source])
            if destination:
                args.extend(["to", destination])
            if mark:
                args.extend(["fwmark", str(mark)])
            if interface:
                args.extend(["iif", interface])

            args.extend(["table", str(table), "prio", str(priority)])

            proc = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            return proc.returncode == 0

        except Exception as e:
            print(f"Failed to add policy rule: {e}")
            return False

    async def setup_load_balancing(
        self,
        gateways: List[Dict[str, str]],
        method: str = "round_robin",  # round_robin, weighted, failover
    ) -> bool:
        """Setup multi-WAN load balancing"""
        try:
            # Create routing tables for each gateway
            for i, gw in enumerate(gateways):
                table_name = f"wan{i + 1}"
                await self.add_routing_table(table_name, 100 + i)

                # Add default route in each table
                await self.add_route(
                    destination="default",
                    gateway=gw["gateway"],
                    interface=gw["interface"],
                    table=table_name,
                )

            if method == "round_robin":
                # Add rules for each connection to different tables
                for i, _ in enumerate(gateways):
                    await self.add_policy_rule(
                        table=100 + i, priority=100 + i, mark=i + 1
                    )

            elif method == "failover":
                # Primary route with higher priority
                await self.add_policy_rule(table=100, priority=100)
                # Backup route
                await self.add_policy_rule(table=101, priority=200)

            return True

        except Exception as e:
            print(f"Load balancing setup failed: {e}")
            return False

    async def get_routes(self, table: str = "all") -> List[Dict[str, Any]]:
        """Get routing table"""
        try:
            args = ["ip", "route", "show"]
            if table != "all":
                args.extend(["table", table])

            proc = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()

            routes = []
            for line in stdout.decode().strip().split("\n"):
                if line and not line.startswith("broadcast"):
                    routes.append({"raw": line})

            return routes
        except:
            return []

    async def get_rules(self) -> List[Dict[str, Any]]:
        """Get policy routing rules"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "rule",
                "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()

            rules = []
            for line in stdout.decode().strip().split("\n"):
                if line:
                    rules.append({"raw": line})

            return rules
        except:
            return []
