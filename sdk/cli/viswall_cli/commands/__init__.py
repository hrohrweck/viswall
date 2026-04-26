from viswall_cli.commands.instances import app as instances_app
from viswall_cli.commands.firewall import app as firewall_app
from viswall_cli.commands.users import app as users_app
from viswall_cli.commands.metrics import app as metrics_app
from viswall_cli.commands.dhcp import app as dhcp_app

__all__ = ["instances_app", "firewall_app", "users_app", "metrics_app", "dhcp_app"]
