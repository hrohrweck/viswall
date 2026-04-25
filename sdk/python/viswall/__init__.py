"""
Viswall Python SDK

A resource-oriented Python SDK for the Viswall distributed security appliance platform.

Example:
    from viswall import ViswallClient

    client = ViswallClient(base_url="https://viswall.example.com", token="your-jwt")
    
    # List instances
    instances = client.instances.list()
    
    # Create a firewall rule
    client.firewall.create_rule(
        instance_id=1,
        name="Allow HTTPS",
        action="accept",
        protocol="tcp",
        dst_port=443
    )
"""

from viswall.client import ViswallClient
from viswall.exceptions import (
    ViswallError,
    ViswallAPIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    "ViswallClient",
    "ViswallError",
    "ViswallAPIError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
]
