"""Proof 1 — certificate auth against AEAT preproducción (T-010, plan §R1).

GOAL: open a client-certificate TLS session to the preproducción VERI*FACTU web
service and get a service-level (non-auth-rejected) SOAP response.

Approach: do a raw mutual-TLS POST of a deliberately minimal SOAP envelope to the
preproducción endpoint. AEAT rejects the (incomplete) payload at schema
validation — BEFORE any record is persisted — so nothing needs annulling. What we
assert is the *handshake*: if the client cert is rejected the TLS handshake fails
(SSLError) or AEAT answers 401/403; if instead we get any SOAP-level response
(200, or 500 + SOAP Fault) we have authenticated and reached the service.

Records the outcome for transcription into docs/changes/T-010/design.md.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])  # poc/aeat-preproduccion on path
import config  # noqa: E402

# Minimal SOAP 1.1 envelope: an empty RegFactu element. Intentionally invalid —
# enough to reach the service and trigger a validation response, not enough to
# create any record.
LR_NS = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/"
    "dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
)
PROBE_ENVELOPE = (
    '<soapenv:Envelope '
    'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    f'xmlns:lr="{LR_NS}">'
    "<soapenv:Body><lr:RegFactuSistemaFacturacion/></soapenv:Body>"
    "</soapenv:Envelope>"
)


def main() -> None:
    try:
        session = config.make_session()
        url = config.endpoint()
    except config.Missing as e:
        config.die(str(e))
        return

    print(f"[T-010 Proof 1] POST (client-cert mTLS) -> {url}")
    try:
        resp = session.post(
            url,
            data=PROBE_ENVELOPE.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "",
            },
            timeout=30,
        )
    except Exception as e:  # noqa: BLE001 — classify any transport/TLS failure
        etype = type(e).__name__
        if "SSL" in etype or "Cert" in etype:
            config.die(
                f"TLS/cert handshake FAILED ({etype}: {e}). Certificate not "
                f"accepted by preproducción — auth NOT proven."
            )
        config.die(f"transport error ({etype}: {e}) — could not reach {url}.")
        return

    body = resp.text or ""
    snippet = body[:600].replace("\n", " ")
    print(f"[T-010 Proof 1] HTTP {resp.status_code} | {len(body)} bytes")
    print(f"[T-010 Proof 1] response head: {snippet}")

    if resp.status_code in (401, 403):
        config.die(
            f"HTTP {resp.status_code} — certificate authenticated at TLS but the "
            f"service REJECTED authorization. Record blocker in design.md."
        )
        return

    # Any SOAP-level answer (incl. a Fault for the bad payload) proves the cert
    # handshake succeeded and we reached the VERI*FACTU service.
    is_soap = "Envelope" in body or "Fault" in body or "RespuestaRegFactu" in body
    if is_soap:
        print(
            "[T-010 Proof 1] PASS: client-cert TLS handshake accepted and a "
            "SOAP-level response was returned (auth proven; payload rejection "
            "at validation is expected for this minimal probe)."
        )
    else:
        print(
            "[T-010 Proof 1] INCONCLUSIVE: handshake completed but the response "
            "is not recognisably SOAP — inspect the body above and record in "
            "design.md."
        )


if __name__ == "__main__":
    main()
