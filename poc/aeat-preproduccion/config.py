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


def make_client():
    """Build a zeep SOAP client bound to a client-cert TLS session.

    SKELETON — wire-up is the developer's first step under Proof 1. The shape:
        from requests import Session
        from requests_pkcs12 import Pkcs12Adapter
        from zeep import Client
        from zeep.transports import Transport
        session = Session()
        session.mount("https://", Pkcs12Adapter(
            pkcs12_filename=cert_path(), pkcs12_password=cert_password()))
        return Client(wsdl_url(), transport=Transport(session=session))
    Returning None here so an un-wired run fails clearly rather than silently.
    """
    raise NotImplementedError(
        "Proof 1 wires the client-cert TLS zeep client here — see docstring."
    )


def die(msg: str) -> None:
    print(f"[T-010 PoC] BLOCKED: {msg}", file=sys.stderr)
    sys.exit(2)
