"""AES-256-GCM envelope encryption for certificate material at rest (T-011).

The encryption key is read from ``settings.CERT_ENCRYPTION_KEY`` (a base64-encoded
32-byte value, distinct from ``SECRET_KEY`` per the T-011 spec). Every ``encrypt``
call generates a fresh 96-bit nonce that ``decrypt`` requires; GCM's auth tag makes
tampering or a wrong key fail loudly (``cryptography.exceptions.InvalidTag``).

This module is the *only* holder of the key. The single sanctioned path to
plaintext certificate material is ``certificates.services`` (least-privilege,
T-011 requirement 3/6).
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

# 96-bit nonce is the GCM-recommended size.
NONCE_BYTES = 12
# AES-256 requires a 32-byte key.
KEY_BYTES = 32


class EncryptionKeyError(RuntimeError):
    """Raised when CERT_ENCRYPTION_KEY is missing or malformed."""


def _load_key() -> bytes:
    raw = getattr(settings, "CERT_ENCRYPTION_KEY", None)
    if not raw:
        raise EncryptionKeyError("CERT_ENCRYPTION_KEY is not configured")
    try:
        key = base64.b64decode(raw, validate=True)
    except (ValueError, TypeError) as exc:
        raise EncryptionKeyError("CERT_ENCRYPTION_KEY is not valid base64") from exc
    if len(key) != KEY_BYTES:
        raise EncryptionKeyError(
            f"CERT_ENCRYPTION_KEY must decode to {KEY_BYTES} bytes (AES-256)"
        )
    return key


def encrypt(plaintext: bytes) -> tuple[bytes, bytes]:
    """Encrypt ``plaintext`` with a fresh nonce; return ``(nonce, ciphertext)``."""
    if not isinstance(plaintext, (bytes, bytearray)):
        raise TypeError("plaintext must be bytes")
    nonce = os.urandom(NONCE_BYTES)
    ciphertext = AESGCM(_load_key()).encrypt(nonce, bytes(plaintext), None)
    return nonce, ciphertext


def decrypt(nonce: bytes, ciphertext: bytes) -> bytes:
    """Decrypt ``ciphertext`` produced by :func:`encrypt`.

    Raises ``cryptography.exceptions.InvalidTag`` if the nonce/ciphertext was
    tampered with or the key differs from the one used to encrypt.
    """
    return AESGCM(_load_key()).decrypt(nonce, ciphertext, None)


def generate_key() -> str:
    """Return a base64-encoded, freshly random 32-byte key (setup/.env helper)."""
    return base64.b64encode(os.urandom(KEY_BYTES)).decode()
