"""Builders for submission tests — a persisted, owned VerifactuRecord.

Reuses the invoicing + compliance factories to produce a *real* ``alta`` record
(issued invoice → ``generate_alta``) whose ``invoice.series.owner`` is a known user,
so the AD-3 owner-resolution chain (design DD2) is exercised end to end.
"""
from compliance import services as compliance_services
from compliance.tests.factories import (
    ISSUER_NAME,
    ISSUER_NIF,
    issued_invoice,
)
from invoicing.tests.factories import make_series, make_user


def make_record(*, owner=None):
    """Create + issue an invoice and persist its alta VerifactuRecord."""
    owner = owner or make_user()
    series = make_series(owner=owner, prefix="SUB")
    invoice = issued_invoice(series=series)
    record = compliance_services.generate_alta(
        invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME
    )
    return record


# --- Fake AEAT response bodies (namespace-agnostic, like the real ones) --------

def _resp(estado_tag, estado, *, csv=None, code=None, desc=None):
    csv_el = f"<CSV>{csv}</CSV>" if csv else ""
    code_el = f"<CodigoErrorRegistro>{code}</CodigoErrorRegistro>" if code else ""
    desc_el = f"<DescripcionErrorRegistro>{desc}</DescripcionErrorRegistro>" if desc else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/"><env:Body>'
        f"<RespuestaRegFactuSistemaFacturacion>{csv_el}"
        f"<RespuestaLinea><{estado_tag}>{estado}</{estado_tag}>{code_el}{desc_el}"
        "</RespuestaLinea></RespuestaRegFactuSistemaFacturacion>"
        "</env:Body></env:Envelope>"
    )


def correcto_body(csv="CSV-OK-123"):
    return _resp("EstadoRegistro", "Correcto", csv=csv)


def aceptado_con_errores_body(csv="CSV-WARN-7", code="0002"):
    return _resp("EstadoRegistro", "AceptadoConErrores", csv=csv, code=code, desc="aviso")


def incorrecto_body(code="3000"):
    return _resp("EstadoRegistro", "Incorrecto", code=code, desc="NIF no censado")
