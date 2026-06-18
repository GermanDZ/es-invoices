"""XAdES-enveloped signing for Verifactu records (T-013 Operation 4).

Signs a built record element (from :mod:`compliance.records`) with the issuer's
qualified certificate and produces a XAdES-BES enveloped XML-DSig signature
(AD-2 "hash-chaining/signing"). The private key is sourced **only** from
:func:`certificates.services.get_cert_material` (T-011 least-privilege) and is
used solely inside :func:`sign_record` — never logged or persisted (T-010 DD2).

signxml operates on lxml elements; ``records`` builds stdlib ``ElementTree``
elements, so we bridge by serialising the (trusted, self-generated) record and
re-parsing it with lxml. Untrusted XML (AEAT responses, externally-supplied
records) must instead be parsed with ``defusedxml`` — see design.md.
"""
from xml.etree import ElementTree as ET

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree
from signxml.xades import XAdESSigner, XAdESVerifier


def _load_p12(cert_material):
    """Decrypt the PKCS#12 material into (private_key, certificate)."""
    passphrase = (cert_material.passphrase or "").encode() or None
    key, cert, _extra = pkcs12.load_key_and_certificates(
        cert_material.p12_bytes, passphrase
    )
    return key, cert


def _to_lxml(element):
    """Convert a stdlib ElementTree element to an lxml element (signxml input)."""
    return etree.fromstring(ET.tostring(element, encoding="utf-8"))


def sign_record(element, cert_material):
    """Return the XAdES-enveloped signed record as a unicode XML string.

    ``element`` is a built ``RegistroAlta`` / ``RegistroAnulacion`` (stdlib ET).
    ``cert_material`` is a :class:`certificates.services.CertMaterial`.
    """
    key, cert = _load_p12(cert_material)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    signed = XAdESSigner().sign(_to_lxml(element), key=key_pem, cert=cert_pem)
    return etree.tostring(signed, encoding="unicode")


def verify_record(signed_xml, certificate_pem):
    """Verify a signed record against ``certificate_pem``.

    Returns the signxml verify result on success; raises (signxml /
    ``cryptography`` exception) when the signature is invalid or the content was
    tampered with.
    """
    data = signed_xml.encode("utf-8") if isinstance(signed_xml, str) else signed_xml
    return XAdESVerifier().verify(
        etree.fromstring(data), x509_cert=certificate_pem
    )


def signer_for_user(user):
    """Build a ``element -> signed_xml`` signer bound to ``user``'s certificate.

    The wiring point for callers (the issue flow / T-014): pass the returned
    callable as ``generate_alta(..., signer=signing.signer_for_user(owner))``.
    """
    from certificates.services import get_cert_material

    cert_material = get_cert_material(user)
    return lambda element: sign_record(element, cert_material)
