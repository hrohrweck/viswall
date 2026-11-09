"""Static assertions on the exim DKIM template (multi-domain signing)."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "config" / "exim4.conf.tmpl"


def test_template_signs_per_sender_domain():
    text = TEMPLATE.read_text()
    assert "dkim_domain = $sender_address_domain" in text
    # Key lookup is guarded by ${if exists{...}}: domains without an installed
    # key expand to an empty string and are simply not signed.
    assert "dkim_private_key = ${if exists{/etc/exim4/dkim/$sender_address_domain.private}" in text


def test_template_has_no_single_domain_placeholder():
    text = TEMPLATE.read_text()
    assert "@@DKIM_DOMAIN@@" not in text
    assert "/etc/exim4/dkim/viswall.private" not in text
