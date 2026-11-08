"""DKIM key material generation for mail domains."""

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

DKIM_SELECTOR = "viswall"


def generate_dkim_keypair() -> tuple[str, str, str]:
    """Generate an RSA-2048 DKIM keypair.

    Returns ``(selector, public_key_b64, private_key_pem)`` where
    ``public_key_b64`` is the base64-encoded DER SubjectPublicKeyInfo — the
    value of the DKIM ``p=`` tag, no PEM headers or whitespace — and
    ``private_key_pem`` is an unencrypted PKCS#8 PEM private key.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_b64 = base64.b64encode(public_der).decode("ascii")
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    return DKIM_SELECTOR, public_key_b64, private_key_pem
