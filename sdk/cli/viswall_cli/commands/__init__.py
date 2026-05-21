from viswall_cli.commands.instances import app as instances_app
from viswall_cli.commands.firewall import app as firewall_app
from viswall_cli.commands.users import app as users_app
from viswall_cli.commands.metrics import app as metrics_app
from viswall_cli.commands.dhcp import app as dhcp_app
from viswall_cli.commands.vpn import app as vpn_app
from viswall_cli.commands.mail import app as mail_app
from viswall_cli.commands.dns import app as dns_app
from viswall_cli.commands.routing import app as routing_app
from viswall_cli.commands.assistant import app as assistant_app
from viswall_cli.commands.audit import app as audit_app
from viswall_cli.commands.groupware import app as groupware_app
from viswall_cli.commands.llm import app as llm_app

__all__ = [
    "instances_app", "firewall_app", "users_app", "metrics_app", "dhcp_app",
    "vpn_app", "mail_app", "dns_app", "routing_app", "assistant_app",
    "audit_app", "groupware_app", "llm_app",
]
