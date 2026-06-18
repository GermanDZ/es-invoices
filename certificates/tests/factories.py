"""Test helpers — build real PKCS#12 material in memory (T-011 Operation 6).

A module-level RSA key is reused across cases (key generation is the slow part);
each helper builds a fresh self-signed certificate with the requested validity so
the upload path exercises genuine ``cryptography`` PKCS#12 loading rather than a
mock.
"""
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _self_signed(not_before, not_after, common_name="Test Autonomo"):
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(_KEY.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .sign(_KEY, hashes.SHA256())
    )


def make_p12(passphrase=b"s3cret", *, expired=False, common_name="Test Autonomo"):
    """Return PKCS#12 bytes for a self-signed cert + key.

    ``expired=True`` builds a certificate whose validity is entirely in the past.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=2)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=365)
    cert = _self_signed(not_before, not_after, common_name)
    encryption = (
        serialization.BestAvailableEncryption(passphrase)
        if passphrase
        else serialization.NoEncryption()
    )
    return pkcs12.serialize_key_and_certificates(
        b"facturasimple-test", _KEY, cert, None, encryption
    )
