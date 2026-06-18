"""Builders for compliance tests — reuse the invoicing factories, then issue."""
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    pkcs12,
)
from cryptography.x509.oid import NameOID

from certificates.services import CertMaterial
from invoicing import services as invoicing_services
from invoicing.tests.factories import make_invoice, make_series, make_user

ISSUER_NIF = "B12345678"
ISSUER_NAME = "Autónomo de Prueba SL"

_NOT_AFTER = datetime.datetime(2030, 1, 1)


def fixture_cert_material(passphrase="testpass"):
    """A self-signed cert wrapped as (CertMaterial, cert_pem) — never a real cert.

    Exercises the real PKCS#12 load path in ``compliance.signing`` (T-010 DD2:
    tests sign with a throwaway fixture, never the founder's qualified cert).
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Fixture Issuer")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime(2026, 1, 1))
        .not_valid_after(_NOT_AFTER)
        .sign(key, hashes.SHA256())
    )
    p12 = pkcs12.serialize_key_and_certificates(
        b"fixture", key, cert, None, BestAvailableEncryption(passphrase.encode())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    material = CertMaterial(
        p12_bytes=p12, passphrase=passphrase, subject="Fixture Issuer",
        not_after=_NOT_AFTER,
    )
    return material, cert_pem


def issued_invoice(*, series=None, lines=None, irpf_rate="0",
                   recipient_name="Cliente SL", recipient_taxid="A82037292"):
    """Create and **issue** an invoice (number assigned, ``issued=True``)."""
    invoice = make_invoice(
        series=series,
        irpf_rate=irpf_rate,
        recipient_name=recipient_name,
        recipient_taxid=recipient_taxid,
        lines=lines or [(1, "100.00", "21")],
    )
    return invoicing_services.issue_invoice(invoice)
