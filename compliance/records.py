"""Verifactu record builders + the ``huella`` hash (T-013 Operation 3).

``compute_huella`` is ported **verbatim** (field order + format) from the T-010
PoC's ``alta_builder.compute_huella``, which AEAT's live ``preproducción``
service accepted for both a first and a chained record (see
``docs/changes/archive/T-010/design.md`` proof 3). The XML builders are adapted
from the same PoC but fed from a T-012 ``Invoice`` + ``invoicing.calc`` totals
instead of hard-coded values.

Built with the standard-library ``xml.etree.ElementTree`` (no third-party XML
runtime dep at this layer). XSD-conformance validation and the XAdES signature
are layered on top in :mod:`compliance.signing` (see the task handoff).

Namespaces mirror the published schema split (``elementFormDefault=qualified``):
  - ``RegFactuSistemaFacturacion`` / ``Cabecera`` / ``RegistroFactura`` → LR
  - ``RegistroAlta`` / ``RegistroAnulacion`` and all children            → SF
"""
import hashlib
from decimal import Decimal
from xml.etree import ElementTree as ET

LR = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
      "dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd")
SF = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
      "dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd")

ET.register_namespace("sfLR", LR)
ET.register_namespace("sf", SF)


def _e(parent, ns, tag, text=None):
    el = ET.SubElement(parent, f"{{{ns}}}{tag}")
    if text is not None:
        el.text = text
    return el


def _d2(value) -> str:
    """Format a Decimal/amount as a 2-decimal string (the AEAT money format)."""
    return str(Decimal(value).quantize(Decimal("0.01")))


def compute_huella(*, id_emisor, num_serie, fecha_exp, tipo_factura,
                   cuota_total, importe_total, huella_anterior, fecha_hora):
    """SHA-256 of the canonical RegistroAlta concatenation → 64-char UPPER hex.

    Field order/format per AEAT 'Veri-Factu_especificaciones_huella_hash'
    (ported from the T-010 PoC, accepted live by AEAT):
      IDEmisorFactura, NumSerieFactura, FechaExpedicionFactura, TipoFactura,
      CuotaTotal, ImporteTotal, Huella (previous; empty for first),
      FechaHoraHusoGenRegistro
    """
    concat = (
        f"IDEmisorFactura={id_emisor}"
        f"&NumSerieFactura={num_serie}"
        f"&FechaExpedicionFactura={fecha_exp}"
        f"&TipoFactura={tipo_factura}"
        f"&CuotaTotal={cuota_total}"
        f"&ImporteTotal={importe_total}"
        f"&Huella={huella_anterior or ''}"
        f"&FechaHoraHusoGenRegistro={fecha_hora}"
    )
    return hashlib.sha256(concat.encode("utf-8")).hexdigest().upper()


def compute_huella_anulacion(*, id_emisor, num_serie, fecha_exp,
                             huella_anterior, fecha_hora):
    """SHA-256 for a RegistroAnulacion (the annulment huella field order).

    Per the AEAT spec a RegistroAnulacion folds in the *annulled* invoice's
    identity (no TipoFactura / amounts), then the chain's previous huella:
      IDEmisorFacturaAnulada, NumSerieFacturaAnulada, FechaExpedicionFacturaAnulada,
      Huella (previous), FechaHoraHusoGenRegistro
    """
    concat = (
        f"IDEmisorFacturaAnulada={id_emisor}"
        f"&NumSerieFacturaAnulada={num_serie}"
        f"&FechaExpedicionFacturaAnulada={fecha_exp}"
        f"&Huella={huella_anterior or ''}"
        f"&FechaHoraHusoGenRegistro={fecha_hora}"
    )
    return hashlib.sha256(concat.encode("utf-8")).hexdigest().upper()


# SIF (Sistema Informático de Facturación) identity — the software producing the
# record. NombreRazon/NIF identify the producer; for v1 we record the issuer as a
# self-developed-style producer (XSD-valid). The FacturaSimple-as-SaaS producer
# fiscal identity is a real-data item flagged in design.md.
SIF_NAME = "FacturaSimple"
SIF_ID = "01"
SIF_VERSION = "1.0"
SIF_INSTALACION = "001"


def _sistema_informatico(parent, issuer_nif, issuer_name):
    """Append the mandatory SistemaInformatico block (SistemaInformaticoType)."""
    si = _e(parent, SF, "SistemaInformatico")
    _e(si, SF, "NombreRazon", issuer_name)
    _e(si, SF, "NIF", issuer_nif)
    _e(si, SF, "NombreSistemaInformatico", SIF_NAME)
    _e(si, SF, "IdSistemaInformatico", SIF_ID)
    _e(si, SF, "Version", SIF_VERSION)
    _e(si, SF, "NumeroInstalacion", SIF_INSTALACION)
    _e(si, SF, "TipoUsoPosibleSoloVerifactu", "S")
    _e(si, SF, "TipoUsoPosibleMultiOT", "N")
    _e(si, SF, "IndicadorMultiplesOT", "N")


def _desglose(alta, groups):
    """Build one DetalleDesglose per IVA rate group (from invoicing.calc)."""
    desg = _e(alta, SF, "Desglose")
    for g in groups:
        det = _e(desg, SF, "DetalleDesglose")
        _e(det, SF, "Impuesto", "01")  # IVA
        _e(det, SF, "ClaveRegimen", "01")  # régimen general
        if Decimal(g.rate) == 0:
            # Exempt / not-subject group. The exact CalificacionOperacion /
            # OperacionExenta code is legal-detail validated against the XSD in
            # the signing/validation handoff; S2 marks "no sujeta"/exenta intent.
            _e(det, SF, "CalificacionOperacion", "S2")
            _e(det, SF, "BaseImponibleOimporteNoSujeto", _d2(g.base))
        else:
            _e(det, SF, "CalificacionOperacion", "S1")  # sujeta y no exenta
            _e(det, SF, "TipoImpositivo", _d2(g.rate))
            _e(det, SF, "BaseImponibleOimporteNoSujeto", _d2(g.base))
            _e(det, SF, "CuotaRepercutida", _d2(g.iva))


def build_registro_alta(*, issuer_nif, issuer_name, num_serie, fecha_exp,
                        fecha_hora, totals, recipient_name, recipient_taxid,
                        descripcion="Factura", previous=None):
    """Return ``(registro_alta_element, huella, cuota_total, importe_total)``.

    ``totals`` is an :class:`invoicing.calc.InvoiceTotals`. ``previous`` is the
    prior :class:`~compliance.models.VerifactuRecord` for this issuer (or None
    for the first record). ImporteTotal is base+IVA (IRPF retention is **not**
    part of the Verifactu importe).
    """
    tipo_factura = "F1"
    cuota_total = _d2(totals.iva_total)
    importe_total = _d2(Decimal(totals.taxable_base) + Decimal(totals.iva_total))
    huella_anterior = previous.huella if previous else None

    huella = compute_huella(
        id_emisor=issuer_nif, num_serie=num_serie, fecha_exp=fecha_exp,
        tipo_factura=tipo_factura, cuota_total=cuota_total,
        importe_total=importe_total, huella_anterior=huella_anterior,
        fecha_hora=fecha_hora,
    )

    alta = ET.Element(f"{{{SF}}}RegistroAlta")
    _e(alta, SF, "IDVersion", "1.0")
    idf = _e(alta, SF, "IDFactura")
    _e(idf, SF, "IDEmisorFactura", issuer_nif)
    _e(idf, SF, "NumSerieFactura", num_serie)
    _e(idf, SF, "FechaExpedicionFactura", fecha_exp)
    _e(alta, SF, "NombreRazonEmisor", issuer_name)
    _e(alta, SF, "TipoFactura", tipo_factura)
    _e(alta, SF, "DescripcionOperacion", descripcion)
    dests = _e(alta, SF, "Destinatarios")
    dest = _e(dests, SF, "IDDestinatario")
    _e(dest, SF, "NombreRazon", recipient_name)
    _e(dest, SF, "NIF", recipient_taxid)
    _desglose(alta, totals.groups)
    _e(alta, SF, "CuotaTotal", cuota_total)
    _e(alta, SF, "ImporteTotal", importe_total)

    enc = _e(alta, SF, "Encadenamiento")
    if previous is not None:
        prev = _e(enc, SF, "RegistroAnterior")
        _e(prev, SF, "IDEmisorFactura", previous.issuer_nif)
        _e(prev, SF, "NumSerieFactura", previous.num_serie)
        _e(prev, SF, "FechaExpedicionFactura", previous.fecha_expedicion)
        _e(prev, SF, "Huella", previous.huella)
    else:
        _e(enc, SF, "PrimerRegistro", "S")

    _sistema_informatico(alta, issuer_nif, issuer_name)
    _e(alta, SF, "FechaHoraHusoGenRegistro", fecha_hora)
    _e(alta, SF, "TipoHuella", "01")  # SHA-256
    _e(alta, SF, "Huella", huella)
    return alta, huella, cuota_total, importe_total


def build_registro_anulacion(*, issuer_nif, issuer_name, num_serie, fecha_exp,
                             fecha_hora, previous=None):
    """Return ``(registro_anulacion_element, huella)`` voiding a prior record.

    References the annulled invoice's identity (IDFactura of the original alta)
    and chains on the issuer's previous huella (UC-005).
    """
    huella_anterior = previous.huella if previous else None
    huella = compute_huella_anulacion(
        id_emisor=issuer_nif, num_serie=num_serie, fecha_exp=fecha_exp,
        huella_anterior=huella_anterior, fecha_hora=fecha_hora,
    )

    anul = ET.Element(f"{{{SF}}}RegistroAnulacion")
    _e(anul, SF, "IDVersion", "1.0")
    idf = _e(anul, SF, "IDFacturaAnulada")
    _e(idf, SF, "IDEmisorFacturaAnulada", issuer_nif)
    _e(idf, SF, "NumSerieFacturaAnulada", num_serie)
    _e(idf, SF, "FechaExpedicionFacturaAnulada", fecha_exp)

    enc = _e(anul, SF, "Encadenamiento")
    if previous is not None:
        prev = _e(enc, SF, "RegistroAnterior")
        _e(prev, SF, "IDEmisorFactura", previous.issuer_nif)
        _e(prev, SF, "NumSerieFactura", previous.num_serie)
        _e(prev, SF, "FechaExpedicionFactura", previous.fecha_expedicion)
        _e(prev, SF, "Huella", previous.huella)
    else:
        _e(enc, SF, "PrimerRegistro", "S")

    _sistema_informatico(anul, issuer_nif, issuer_name)
    _e(anul, SF, "FechaHoraHusoGenRegistro", fecha_hora)
    _e(anul, SF, "TipoHuella", "01")
    _e(anul, SF, "Huella", huella)
    return anul, huella


def wrap_envelope(registros, *, issuer_nif, issuer_name):
    """Wrap built record element(s) in a `RegFactuSistemaFacturacion` envelope.

    The submission/XSD-validation unit: `Cabecera` (the obligado emisor) + one
    `RegistroFactura` per record. Each ``registros`` element is an `sf`-namespaced
    `RegistroAlta`/`RegistroAnulacion` from the builders above.
    """
    root = ET.Element(f"{{{LR}}}RegFactuSistemaFacturacion")
    cab = _e(root, LR, "Cabecera")
    obl = _e(cab, SF, "ObligadoEmision")
    _e(obl, SF, "NombreRazon", issuer_name)
    _e(obl, SF, "NIF", issuer_nif)
    for registro in registros:
        rf = _e(root, LR, "RegistroFactura")
        rf.append(registro)
    return root


def serialize(element) -> str:
    """UTF-8 string form of a built record element."""
    return ET.tostring(element, encoding="unicode")
