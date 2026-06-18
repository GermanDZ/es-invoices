"""T-017 requirement 2 — the rectificativa-type *alta* record.

A factura rectificativa is a Verifactu *alta* with ``TipoFactura=R1``,
``TipoRectificativa=S`` and a ``FacturasRectificadas`` reference to the rectified
invoice's original alta (UC-004). These tests assert the generated record carries
that metadata, chains over the issuer's prior huella, folds the R1 tipo into the
huella, and stays XSD-conformant against the vendored AEAT schema.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

from django.test import TestCase
from lxml import etree

import compliance
from compliance import records
from compliance.models import VerifactuRecord
from compliance.records import SF, compute_huella
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF, issued_invoice
from invoicing.tests.factories import make_series

SCHEMA_PATH = Path(__file__).parent / "fixtures" / "SuministroLR.xsd"
FECHA_HORA = "2026-06-18T12:00:00+02:00"


def _find(elem, tag):
    return elem.find(f".//{{{SF}}}{tag}")


class RectificativaRecordTests(TestCase):
    def setUp(self):
        # Original sale in the default series; rectificativa in its own series so
        # both share the issuer chain but carry distinct num_serie.
        self.original = issued_invoice(lines=[(1, "100.00", "21")])
        self.original_rec = compliance.generate_alta(
            self.original, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self.rect_series = make_series(owner=self.original.series.owner, prefix="REC")
        self.rect = issued_invoice(series=self.rect_series, lines=[(1, "80.00", "21")])

    def _rectificativa(self):
        return compliance.generate_alta(
            self.rect, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA, tipo_factura="R1", tipo_rectificativa="S",
            rectifies=self.original_rec,
        )

    def test_record_carries_rectificativa_metadata_and_reference(self):
        rec = self._rectificativa()
        self.assertEqual(rec.record_type, VerifactuRecord.ALTA)
        self.assertEqual(rec.tipo_factura, "R1")

        root = ET.fromstring(rec.xml)
        self.assertEqual(_find(root, "TipoFactura").text, "R1")
        self.assertEqual(_find(root, "TipoRectificativa").text, "S")
        rects = _find(root, "FacturasRectificadas")
        self.assertIsNotNone(rects)
        idr = _find(rects, "IDFacturaRectificada")
        self.assertEqual(_find(idr, "NumSerieFactura").text, self.original_rec.num_serie)
        self.assertEqual(
            _find(idr, "FechaExpedicionFactura").text,
            self.original_rec.fecha_expedicion,
        )
        # Sustitución carries the substituted (original) base + cuota.
        imp = _find(root, "ImporteRectificacion")
        self.assertEqual(_find(imp, "BaseRectificada").text, "100.00")
        self.assertEqual(_find(imp, "CuotaRectificada").text, "21.00")

    def test_rectificativa_chains_over_prior_huella(self):
        rec = self._rectificativa()
        self.assertEqual(rec.previous_record_id, self.original_rec.id)
        self.assertEqual(rec.previous_huella, self.original_rec.huella)
        self.assertNotEqual(rec.huella, self.original_rec.huella)

    def test_huella_folds_the_r1_tipo(self):
        rec = self._rectificativa()
        expected = compute_huella(
            id_emisor=ISSUER_NIF, num_serie=rec.num_serie,
            fecha_exp=rec.fecha_expedicion, tipo_factura="R1",
            cuota_total=rec.cuota_total, importe_total=rec.importe_total,
            huella_anterior=self.original_rec.huella, fecha_hora=FECHA_HORA,
        )
        self.assertEqual(rec.huella, expected)

    def test_rectificativa_envelope_is_xsd_conformant(self):
        rec = self._rectificativa()
        registro = ET.fromstring(rec.xml)
        env = records.wrap_envelope(
            [registro], issuer_nif=rec.issuer_nif, issuer_name=rec.issuer_name
        )
        schema = etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))
        doc = etree.fromstring(ET.tostring(env, encoding="utf-8"))
        ok = schema.validate(doc)
        errors = [e.message for e in schema.error_log]
        self.assertTrue(ok, f"XSD validation failed: {errors[:3]}")
