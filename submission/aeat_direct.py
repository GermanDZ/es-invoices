"""The AD-3 v1 adapter: direct AEAT VERI*FACTU submission (T-014 Operation 3).

Productionizes the proven T-010 PoC transport — mutual-TLS ``.p12`` session, a
hand-built SOAP 1.1 envelope, and a namespace-agnostic response parse — as tested
module code. The adapter is a *pure transport*: it neither generates nor signs the
record (AD-2 / T-013 owns that) nor manages certificates (T-011). It:

1. resolves the owner from the record (``invoice.series.owner``) and pulls the
   PKCS#12 material through ``certificates.services.get_cert_material`` — the sole
   sanctioned plaintext path;
2. re-wraps the stored ``record.xml`` (a bare, optionally-signed ``RegistroAlta``)
   in the full ``RegFactuSistemaFacturacion`` via ``compliance.records.wrap_envelope``
   — appended unmodified, so any enveloped signature stays valid (design DD1) — then
   in the SOAP envelope;
3. POSTs over the mTLS session and parses the estado / error code / CSV.

The transport call is injectable (``transport=``) so the unit suite drives outcome
parsing and retry without a real certificate or a live AEAT.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from lxml import etree

from compliance import records as compliance_records

from .gateway import SubmissionGateway, SubmissionOutcome, SubmissionStatus

SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"


class SubmissionTransportError(Exception):
    """A transport-level failure (timeout / connection / HTTP 5xx / unparseable).

    Raised by the adapter so :mod:`submission.services` can apply the bounded
    retry → ``pending`` policy. A *business* rejection is NOT this — it returns a
    ``SubmissionOutcome(status=REJECTED)``.
    """


def _owner_of(record):
    """The User whose certificate signs the mTLS session (design DD2)."""
    return record.invoice.series.owner


def _build_soap_payload(record) -> bytes:
    """Wrap the stored RegistroAlta in RegFactu, then in a SOAP 1.1 envelope."""
    # wrap_envelope builds with stdlib ElementTree, so the stored registro is parsed
    # with ET (not lxml) and appended unmodified — huella/signature untouched (DD1).
    # record.xml is trusted, self-generated content from the compliance module (our
    # own DB), not external input — no XXE surface here.
    registro = ET.fromstring(record.xml)
    regfactu = compliance_records.wrap_envelope(
        [registro], issuer_nif=record.issuer_nif, issuer_name=record.issuer_name
    )
    # Bridge ET → lxml by serialise→parse (trusted, self-generated XML) so the SOAP
    # body carries one consistent tree.
    regfactu_xml = compliance_records.serialize(regfactu)
    body_el = etree.fromstring(regfactu_xml.encode("utf-8"))

    env = etree.Element(f"{{{SOAP_NS}}}Envelope", nsmap={"soapenv": SOAP_NS})
    body = etree.SubElement(env, f"{{{SOAP_NS}}}Body")
    body.append(body_el)
    return etree.tostring(env, xml_declaration=True, encoding="UTF-8")


def parse_response(text: str) -> dict:
    """Pull the salient fields from an AEAT response (namespace-agnostic).

    Ported from the PoC ``alta_builder.parse_response``. Returns a dict that may
    carry ``EstadoEnvio`` / ``EstadoRegistro`` / ``CSV`` / ``CodigoErrorRegistro`` /
    ``DescripcionErrorRegistro`` / ``faultstring``.
    """
    out: dict = {}
    # The AEAT response is the one genuinely untrusted input here — parse it with a
    # hardened parser: no external-entity resolution, no network, no huge-tree
    # expansion (defuses XXE + billion-laughs).
    safe_parser = etree.XMLParser(
        resolve_entities=False, no_network=True, huge_tree=False, dtd_validation=False
    )
    try:
        root = etree.fromstring(text.encode("utf-8"), parser=safe_parser)
    except Exception:  # noqa: BLE001 — malformed body is a transport-level fault
        return {"_raw": text[:800]}

    def first(local):
        for el in root.iter():
            if isinstance(el.tag, str) and etree.QName(el).localname == local and el.text:
                return el.text.strip()
        return None

    for key in (
        "EstadoEnvio", "CSV", "EstadoRegistro", "CodigoErrorRegistro",
        "DescripcionErrorRegistro", "faultstring",
    ):
        val = first(key)
        if val:
            out[key] = val
    return out


def outcome_from_response(parsed: dict, *, retries: int = 0) -> SubmissionOutcome:
    """Map a parsed AEAT response to a verdict (design DD4).

    Per-record ``EstadoRegistro`` wins, falling back to the envelope ``EstadoEnvio``.
    ``Correcto`` / ``AceptadoConErrores`` → accepted; ``Incorrecto`` → rejected. A
    response with no estado at all is a transport-level fault (raises, so the caller
    retries) — a verdict-less 200 is not an acceptance.
    """
    estado = parsed.get("EstadoRegistro") or parsed.get("EstadoEnvio")
    if estado in ("Correcto", "AceptadoConErrores"):
        return SubmissionOutcome(
            status=SubmissionStatus.ACCEPTED,
            estado=estado,
            aeat_code=parsed.get("CodigoErrorRegistro"),
            aeat_message=parsed.get("DescripcionErrorRegistro"),
            csv=parsed.get("CSV"),
            retries=retries,
            raw=parsed,
        )
    if estado in ("Incorrecto", "Rechazado"):
        return SubmissionOutcome(
            status=SubmissionStatus.REJECTED,
            estado=estado,
            aeat_code=parsed.get("CodigoErrorRegistro"),
            aeat_message=parsed.get("DescripcionErrorRegistro") or parsed.get("faultstring"),
            retries=retries,
            raw=parsed,
        )
    # No estado → the AEAT did not register a verdict; treat as transport fault.
    raise SubmissionTransportError(
        f"AEAT response carried no estado: {parsed.get('faultstring') or parsed!r:.200}"
    )


def _default_transport(url: str, soap_bytes: bytes, *, cert_material, timeout: int) -> str:
    """Real mTLS POST to the AEAT using the user's PKCS#12 (design DD3).

    The decrypted ``.p12`` bytes are handed to ``requests_pkcs12`` in memory — never
    written to disk. Network/transport errors surface as
    :class:`SubmissionTransportError`.
    """
    import requests
    from requests import Session
    from requests_pkcs12 import Pkcs12Adapter

    session = Session()
    session.mount(
        "https://",
        Pkcs12Adapter(
            pkcs12_data=cert_material.p12_bytes,
            pkcs12_password=cert_material.passphrase or None,
        ),
    )
    try:
        resp = session.post(
            url,
            data=soap_bytes,
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise SubmissionTransportError(str(exc)) from exc
    if resp.status_code >= 500:
        raise SubmissionTransportError(f"AEAT HTTP {resp.status_code}")
    return resp.text


class AeatDirectAdapter(SubmissionGateway):
    """Submit one record to the AEAT over mutual-TLS SOAP."""

    def __init__(self, *, endpoint: str, timeout: int = 45, transport=None):
        self.endpoint = endpoint
        self.timeout = timeout
        # transport(url, soap_bytes, *, cert_material, timeout) -> response_text
        self._transport = transport or _default_transport

    def submit(self, record) -> SubmissionOutcome:
        from certificates.services import get_cert_material

        cert_material = get_cert_material(_owner_of(record))  # CertificateNotConfigured propagates
        soap_bytes = _build_soap_payload(record)
        text = self._transport(
            self.endpoint, soap_bytes, cert_material=cert_material, timeout=self.timeout
        )
        parsed = parse_response(text)
        return outcome_from_response(parsed)
