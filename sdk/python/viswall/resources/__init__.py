"""Viswall SDK resources."""

from viswall.resources.auth import AuthResource
from viswall.resources.instances import InstancesResource
from viswall.resources.users import UsersResource
from viswall.resources.firewall import FirewallResource
from viswall.resources.routing import RoutingResource
from viswall.resources.mail import MailResource
from viswall.resources.metrics import MetricsResource
from viswall.resources.audit import AuditResource
from viswall.resources.vpn import VPNResource
from viswall.resources.assistant import AssistantResource
from viswall.resources.groupware import GroupwareResource

__all__ = [
    "AuthResource",
    "InstancesResource",
    "UsersResource",
    "FirewallResource",
    "RoutingResource",
    "MailResource",
    "MetricsResource",
    "AuditResource",
    "VPNResource",
    "AssistantResource",
    "GroupwareResource",
]
