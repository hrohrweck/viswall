"""Viswall VPN agent — WireGuard site-to-site CLIENT tunnel manager.

Ownership model: the ``wg-quick@client`` systemd unit remains the single
lifecycle owner of the tunnel. This agent only (a) renders and atomically
writes ``/etc/wireguard/client.conf`` and (b) steers that unit
(restart/enable/disable via ``nsenter -t 1 -m -u -i -n -- systemctl ...``).
It never runs ``wg-quick up/down`` itself.
"""

__version__ = "1.0.0"
