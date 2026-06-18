"""Persistence for user AEAT certificates (T-011 Operation 3).

A ``UserCertificate`` holds the qualified certificate (PKCS#12 bytes) and its
passphrase **encrypted at rest** (AES-256-GCM, see ``certificates.crypto``),
each in its own ciphertext column with a per-record nonce. Only
``certificates.services`` ever encrypts into or decrypts out of these columns
(least-privilege, T-011 requirements 3 & 6) — the model itself is pure storage
and never holds plaintext.

One active certificate per user (``OneToOneField``): re-uploading overwrites the
prior material; deleting the owning user cascades the certificate away (the
retention boundary for R-06).
"""
from django.conf import settings
from django.db import models


class UserCertificate(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificate",
    )

    # Encrypted material — never plaintext. Each blob carries its own nonce.
    cert_nonce = models.BinaryField()
    cert_ciphertext = models.BinaryField()
    passphrase_nonce = models.BinaryField()
    passphrase_ciphertext = models.BinaryField()

    # Plaintext metadata extracted at upload so status/expiry never require a
    # decrypt. Not secret on its own.
    subject = models.CharField(max_length=512)
    not_after = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Certificate for {self.owner} (expires {self.not_after:%Y-%m-%d})"
