"""Requirement 3 — a generated RegistroAlta validates against the published XSD.

Validates the full `RegFactuSistemaFacturacion` envelope (the submission unit)
against the vendored AEAT schemas (`compliance/tests/fixtures/`). `ds:Signature`
is `minOccurs=0` in the schema, so the unsigned envelope is XSD-conformant; the
signature itself is covered by `test_signing`.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

from django.test import TestCase
from lxml import etree

import compliance
from compliance import records
from compliance.models import VerifactuRecord
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF, issued_invoice

SCHEMA_PATH = Path(__file__).parent / "fixtures" / "SuministroLR.xsd"
FECHA_HORA = "2026-06-18T12:00:00+02:00"


def _schema():
    return etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))


def _envelope_for(record: VerifactuRecord):
    """Re-parse the persisted record XML and wrap it for envelope validation."""
    registro = ET.fromstring(record.xml)
    env = records.wrap_envelope(
        [registro], issuer_nif=record.issuer_nif, issuer_name=record.issuer_name
    )
    return etree.fromstring(ET.tostring(env, encoding="utf-8"))


class XsdConformanceTests(TestCase):
    def _assert_valid(self, record):
        schema = _schema()
        doc = _envelope_for(record)
        ok = schema.validate(doc)
        errors = [e.message for e in schema.error_log]
        self.assertTrue(ok, f"XSD validation failed: {errors[:3]}")

    def test_single_rate_alta_is_xsd_conformant(self):
        invoice = issued_invoice(lines=[(1, "100.00", "21")])
        record = compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self._assert_valid(record)

    def test_multi_rate_with_exempt_alta_is_xsd_conformant(self):
        # The R3 scenario: two 21% lines + one exempt → two DetalleDesglose.
        invoice = issued_invoice(
            lines=[(1, "100.00", "21"), (1, "50.00", "21"), (1, "30.00", "0")]
        )
        record = compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self._assert_valid(record)
