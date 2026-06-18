"""Requirement 4 (huella) + Requirement 3 (per-group Desglose structure).

The XSD-conformance half of Requirement 3 and the signature (Requirement 6) are
covered once the XSD is vendored and the XAdES signer lands — see the handoff.
Here we prove the huella reproduces the AEAT field concatenation byte-for-byte
and the Desglose mirrors invoicing.calc's rate groups.
"""
import hashlib
from decimal import Decimal
from xml.etree import ElementTree as ET

from django.test import TestCase

import compliance
from compliance.records import SF
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF, issued_invoice

FECHA_HORA = "2026-06-18T12:00:00+02:00"


def _find(elem, tag):
    return elem.find(f".//{{{SF}}}{tag}")


def _findall(elem, tag):
    return elem.findall(f".//{{{SF}}}{tag}")


class HuellaTests(TestCase):
    def test_first_record_huella_matches_spec_concatenation(self):
        invoice = issued_invoice(lines=[(1, "100.00", "21")])
        rec = compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        fecha_exp = invoice.issue_date.strftime("%d-%m-%Y")
        expected_concat = (
            f"IDEmisorFactura={ISSUER_NIF}"
            f"&NumSerieFactura={rec.num_serie}"
            f"&FechaExpedicionFactura={fecha_exp}"
            f"&TipoFactura=F1"
            f"&CuotaTotal=21.00"
            f"&ImporteTotal=121.00"
            f"&Huella="
            f"&FechaHoraHusoGenRegistro={FECHA_HORA}"
        )
        expected = hashlib.sha256(expected_concat.encode("utf-8")).hexdigest().upper()
        self.assertEqual(rec.huella, expected)
        self.assertEqual(len(rec.huella), 64)

    def test_first_record_marks_primer_registro(self):
        invoice = issued_invoice()
        rec = compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        root = ET.fromstring(rec.xml)
        self.assertIsNotNone(_find(root, "PrimerRegistro"))
        self.assertIsNone(_find(root, "RegistroAnterior"))


class DesgloseTests(TestCase):
    def test_one_detalle_per_rate_group_matching_calc(self):
        # Two 21% lines + one exempt → two rate groups (21, 0).
        invoice = issued_invoice(
            lines=[(1, "100.00", "21"), (1, "50.00", "21"), (1, "30.00", "0")]
        )
        rec = compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        root = ET.fromstring(rec.xml)
        detalles = _findall(root, "DetalleDesglose")
        self.assertEqual(len(detalles), 2)

        totals = invoice.compute_totals()
        by_rate = {Decimal(g.rate): g for g in totals.groups}
        # 21% group: base 150.00, cuota 31.50.
        g21 = by_rate[Decimal("21")]
        self.assertEqual(g21.base, Decimal("150.00"))
        self.assertEqual(g21.iva, Decimal("31.50"))
        # Importe persisted = base + iva (IRPF excluded from Verifactu importe).
        self.assertEqual(
            Decimal(rec.importe_total),
            totals.taxable_base + totals.iva_total,
        )
        self.assertEqual(Decimal(rec.cuota_total), totals.iva_total)
