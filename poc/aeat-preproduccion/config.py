"""Shared config + session setup for the AEAT preproducción PoC (T-010).

THROWAWAY PoC — not production code. Centralises certificate + endpoint
resolution so the three proof scripts share one client-cert TLS session.

All secrets come from the environment / a local path; nothing secret is ever
written into the repo (see repo .gitignore).
"""
import os
import sys


class Missing(RuntimeError):
    """A required env var / file is absent — fail loudly, never guess."""


def _require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise Missing(
            f"env var {name} is not set. See poc/aeat-preproduccion/README.md "
            f"(Configuration). The PoC needs a founder-supplied certificate + "
            f"the current preproducción WSDL URL."
        )
    return val


def cert_path() -> str:
    path = _require_env("AEAT_CERT_PATH")
    if not os.path.isfile(path):
        raise Missing(f"AEAT_CERT_PATH={path!r} does not point at a readable file.")
    return path


def cert_password() -> str:
    # Optional — a passphrase-less test cert is allowed.
    return os.environ.get("AEAT_CERT_PASSWORD", "")


def wsdl_url() -> str:
    # Resolve the CURRENT preproducción WSDL at run time — do not hard-code
    # (the spec moved; see T-007 O-2). Record the URL used in design.md.
    return _require_env("AEAT_WSDL_URL")


def emisor_nif() -> str:
    return _require_env("AEAT_NIF")


# --- preproducción binding -------------------------------------------------
# The WSDL bundles BOTH environments. zeep's default `client.service` binds the
# FIRST port — `SistemaVerifactu`, which is PRODUCTION (www1). Sending test data
# there creates real records that must be annulled (AEAT FAQ). So every proof
# MUST bind the preproducción port explicitly. Qualified-cert sandbox port:
PRUEBAS_SERVICE = "sfVerifactu"
PRUEBAS_PORT = "SistemaVerifactuPruebas"  # NOT *SelloPruebas (that is for sello certs)
PRUEBAS_ADDRESS = (
    "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
)


def make_session():
    """A requests Session doing client-cert (.p12) mutual TLS to AEAT."""
    from requests import Session
    from requests_pkcs12 import Pkcs12Adapter

    session = Session()
    session.mount(
        "https://",
        Pkcs12Adapter(
            pkcs12_filename=cert_path(),
            pkcs12_password=cert_password() or None,
        ),
    )
    return session


def make_client():
    """Build a zeep client + a service proxy BOUND TO PREPRODUCCIÓN.

    Returns (client, service). `service` is bound to the `SistemaVerifactuPruebas`
    port (prewww1) — never the production default. Use `service` for SOAP ops and
    `make_session()` for low-level probes.
    """
    from zeep import Client
    from zeep.transports import Transport

    session = make_session()
    client = Client(wsdl_url(), transport=Transport(session=session))
    service = client.bind(PRUEBAS_SERVICE, PRUEBAS_PORT)
    return client, service


def endpoint() -> str:
    """The preproducción address proofs actually POST to (for logging)."""
    return PRUEBAS_ADDRESS


def cert_identity():
    """(nif, nombre) read from the certificate's PUBLIC subject — never printed.

    Used so the submitted record's ObligadoEmision matches the cert's census
    identity (avoids a NIF/name-mismatch rejection). Only the public cert is
    inspected; the private key is irrelevant here. RGPD: callers must NOT log the
    returned name/NIF — record only masked/aggregate evidence.
    """
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID

    with open(cert_path(), "rb") as fh:
        data = fh.read()
    pwd = cert_password()
    _key, cert, _chain = pkcs12.load_key_and_certificates(
        data, pwd.encode() if pwd else None
    )
    subj = cert.subject

    def attr(oid):
        vals = subj.get_attributes_for_oid(oid)
        return vals[0].value if vals else None

    # FNMT serialNumber is like "IDCES-12345678Z" or "12345678Z".
    raw_nif = attr(NameOID.SERIAL_NUMBER) or ""
    nif = raw_nif.split("-")[-1].strip().upper()
    given = (attr(NameOID.GIVEN_NAME) or "").strip()
    surname = (attr(NameOID.SURNAME) or "").strip()
    if surname or given:
        nombre = f"{surname} {given}".strip()          # census order: apellidos nombre
    else:
        cn = (attr(NameOID.COMMON_NAME) or "").strip()
        nombre = cn.split(" - ")[0].strip()            # drop the "- NIF" suffix
    # Fall back to the env NIF only if the cert had none.
    return (nif or emisor_nif()), nombre


def die(msg: str) -> None:
    print(f"[T-010 PoC] BLOCKED: {msg}", file=sys.stderr)
    sys.exit(2)
