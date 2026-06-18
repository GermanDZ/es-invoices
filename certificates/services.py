"""The single sanctioned path to certificate plaintext (T-011 Operation 5).

Every encrypt-into / decrypt-out-of ``UserCertificate`` goes through here, so
least-privilege (requirements 3 & 6) is structural: views, forms, serializers,
and logs never touch ``certificates.crypto.decrypt`` directly. The future AEAT
submission adapter (T-014, behind AD-3) consumes :func:`get_cert_material`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .crypto import decrypt, encrypt
from .models import UserCertificate


class CertificateNotConfigured(Exception):
    """Raised when plaintext is requested for a user with no stored certificate."""


@dataclass(frozen=True)
class CertMaterial:
    """Decrypted certificate material, ready for an mTLS session."""

    p12_bytes: bytes
    passphrase: str
    subject: str
    not_after: datetime


def store_certificate(
    user,
    *,
    p12_bytes: bytes,
    passphrase: str,
    subject: str,
    not_after: datetime,
) -> UserCertificate:
    """Encrypt and persist (or replace) the certificate for ``user``."""
    cert_nonce, cert_ct = encrypt(p12_bytes)
    pass_nonce, pass_ct = encrypt(passphrase.encode())
    obj, _ = UserCertificate.objects.update_or_create(
        owner=user,
        defaults={
            "cert_nonce": cert_nonce,
            "cert_ciphertext": cert_ct,
            "passphrase_nonce": pass_nonce,
            "passphrase_ciphertext": pass_ct,
            "subject": subject,
            "not_after": not_after,
        },
    )
    return obj


def get_cert_material(user) -> CertMaterial:
    """Return decrypted material for ``user`` (the sole plaintext path).

    Raises :class:`CertificateNotConfigured` when nothing is stored, rather than
    returning an empty/plaintext-null record.
    """
    try:
        rec = UserCertificate.objects.get(owner=user)
    except UserCertificate.DoesNotExist as exc:
        raise CertificateNotConfigured(
            "No certificate is configured for this user"
        ) from exc
    p12_bytes = decrypt(bytes(rec.cert_nonce), bytes(rec.cert_ciphertext))
    passphrase = decrypt(
        bytes(rec.passphrase_nonce), bytes(rec.passphrase_ciphertext)
    ).decode()
    return CertMaterial(
        p12_bytes=p12_bytes,
        passphrase=passphrase,
        subject=rec.subject,
        not_after=rec.not_after,
    )


def certificate_status(user) -> str:
    """``"configured"`` if the user has a stored certificate, else ``"not-configured"``.

    Checks UC-002's precondition without decrypting anything.
    """
    if user.is_authenticated and UserCertificate.objects.filter(owner=user).exists():
        return "configured"
    return "not-configured"


def delete_certificate(user) -> None:
    """Remove the user's stored (encrypted) certificate, if any."""
    UserCertificate.objects.filter(owner=user).delete()
