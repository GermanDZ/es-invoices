"""Build + sign-by-hash a VERI*FACTU `RegistroAlta` for the preproducción PoC.

THROWAWAY PoC code (T-010). Constructs a minimal-but-XSD-conformant
`RegFactuSistemaFacturacion` envelope carrying one `alta` record, computes the
`huella` per the AEAT spec, and validates locally against the published XSD.

Namespaces (elementFormDefault=qualified in both schemas):
  - RegFactuSistemaFacturacion, Cabecera, RegistroFactura  -> SuministroLR.xsd (LR)
  - RegistroAlta + all its children                        -> SuministroInformacion.xsd (SF)
"""
import hashlib
import os
from lxml import etree

LR = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
      "dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd")
SF = ("https://www2.agenciatributaria.gob.es/static_files/common/internet/"
      "dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd")

WSDL_DIR = os.path.join(os.path.dirname(__file__), "secrets", "wsdl")
_NSMAP = {"sfLR": LR, "sf": SF}


def _lr(tag):
    return etree.SubElement if False else f"{{{LR}}}{tag}"


def _e(parent, ns, tag, text=None):
    el = etree.SubElement(parent, f"{{{ns}}}{tag}")
    if text is not None:
        el.text = text
    return el


def compute_huella(*, id_emisor, num_serie, fecha_exp, tipo_factura,
                   cuota_total, importe_total, huella_anterior, fecha_hora):
    """SHA-256 of the canonical RegistroAlta concatenation → 64-char UPPER hex.

    Field order/format per AEAT 'Veri-Factu_especificaciones_huella_hash':
      IDEmisorFactura, NumSerieFactura, FechaExpedicionFactura, TipoFactura,
      CuotaTotal, ImporteTotal, Huella (previous; empty for first), FechaHoraHusoGenRegistro
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


def build_regfactu(*, nif, nombre, num_serie, fecha_exp, fecha_hora,
                   base="100.00", tipo_iva="21.00", cuota="21.00",
                   total="121.00", huella_anterior=None, serie_anterior=None,
                   fecha_anterior=None):
    """Return (regfactu_element, huella) for one alta record.

    huella_anterior/serie_anterior/fecha_anterior set => chained (RegistroAnterior);
    otherwise PrimerRegistro=S.
    """
    tipo_factura = "F1"
    huella = compute_huella(
        id_emisor=nif, num_serie=num_serie, fecha_exp=fecha_exp,
        tipo_factura=tipo_factura, cuota_total=cuota, importe_total=total,
        huella_anterior=huella_anterior, fecha_hora=fecha_hora,
    )

    root = etree.Element(f"{{{LR}}}RegFactuSistemaFacturacion", nsmap=_NSMAP)
    cab = _e(root, LR, "Cabecera")
    obl = _e(cab, SF, "ObligadoEmision")
    _e(obl, SF, "NombreRazon", nombre)
    _e(obl, SF, "NIF", nif)

    rf = _e(root, LR, "RegistroFactura")
    alta = _e(rf, SF, "RegistroAlta")
    _e(alta, SF, "IDVersion", "1.0")
    idf = _e(alta, SF, "IDFactura")
    _e(idf, SF, "IDEmisorFactura", nif)
    _e(idf, SF, "NumSerieFactura", num_serie)
    _e(idf, SF, "FechaExpedicionFactura", fecha_exp)
    _e(alta, SF, "NombreRazonEmisor", nombre)
    _e(alta, SF, "TipoFactura", tipo_factura)
    _e(alta, SF, "DescripcionOperacion", "PoC T-010 preproduccion submission test")
    # F1 requires a Destinatarios block (AEAT error 1189). A Spanish NIF is
    # census-checked (error 1239 if unknown), so the PoC uses a real, public
    # census-identified company NIF as the test recipient.
    dests = _e(alta, SF, "Destinatarios")
    dest = _e(dests, SF, "IDDestinatario")
    _e(dest, SF, "NombreRazon", "MEDIA MARKT SATURN SA")
    _e(dest, SF, "NIF", "A82037292")
    desg = _e(alta, SF, "Desglose")
    det = _e(desg, SF, "DetalleDesglose")
    _e(det, SF, "Impuesto", "01")            # IVA
    _e(det, SF, "ClaveRegimen", "01")        # régimen general
    _e(det, SF, "CalificacionOperacion", "S1")  # sujeta y no exenta
    _e(det, SF, "TipoImpositivo", tipo_iva)
    _e(det, SF, "BaseImponibleOimporteNoSujeto", base)
    _e(det, SF, "CuotaRepercutida", cuota)
    _e(alta, SF, "CuotaTotal", cuota)
    _e(alta, SF, "ImporteTotal", total)

    enc = _e(alta, SF, "Encadenamiento")
    if huella_anterior:
        prev = _e(enc, SF, "RegistroAnterior")
        _e(prev, SF, "IDEmisorFactura", nif)
        _e(prev, SF, "NumSerieFactura", serie_anterior)
        _e(prev, SF, "FechaExpedicionFactura", fecha_anterior)
        _e(prev, SF, "Huella", huella_anterior)
    else:
        _e(enc, SF, "PrimerRegistro", "S")

    si = _e(alta, SF, "SistemaInformatico")
    _e(si, SF, "NombreRazon", nombre)
    _e(si, SF, "NIF", nif)
    _e(si, SF, "NombreSistemaInformatico", "FacturaSimple PoC")
    _e(si, SF, "IdSistemaInformatico", "01")
    _e(si, SF, "Version", "0.1")
    _e(si, SF, "NumeroInstalacion", "001")
    _e(si, SF, "TipoUsoPosibleSoloVerifactu", "S")
    _e(si, SF, "TipoUsoPosibleMultiOT", "N")
    _e(si, SF, "IndicadorMultiplesOT", "N")

    _e(alta, SF, "FechaHoraHusoGenRegistro", fecha_hora)
    _e(alta, SF, "TipoHuella", "01")         # SHA-256
    _e(alta, SF, "Huella", huella)
    return root, huella


def validate_local(regfactu_element):
    """Validate against the local SuministroLR.xsd. Returns (ok, [errors])."""
    schema = etree.XMLSchema(etree.parse(os.path.join(WSDL_DIR, "SuministroLR.xsd")))
    ok = schema.validate(regfactu_element)
    return ok, [f"{e.message} (line {e.line})" for e in schema.error_log]


def soap_envelope(regfactu_element):
    """Wrap the RegFactu element in a SOAP 1.1 envelope; return bytes."""
    env = etree.Element("{http://schemas.xmlsoap.org/soap/envelope/}Envelope",
                        nsmap={"soapenv": "http://schemas.xmlsoap.org/soap/envelope/"})
    body = etree.SubElement(env, "{http://schemas.xmlsoap.org/soap/envelope/}Body")
    body.append(regfactu_element)
    return etree.tostring(env, xml_declaration=True, encoding="UTF-8")


def parse_response(text):
    """Pull the salient fields out of an AEAT response (namespace-agnostic)."""
    out = {}
    try:
        root = etree.fromstring(text.encode("utf-8"))
    except Exception:  # noqa: BLE001
        return {"_raw": text[:800]}
    def first(local):
        for el in root.iter():
            if etree.QName(el).localname == local and el.text:
                return el.text.strip()
        return None
    for k in ("EstadoEnvio", "CSV", "EstadoRegistro", "CodigoErrorRegistro",
              "DescripcionErrorRegistro", "faultstring"):
        v = first(k)
        if v:
            out[k] = v
    return out
