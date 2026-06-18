"""Requirement 5 (hash-chain linkage) + Requirement 7 (annulment record).

Deterministic linkage is covered here. The fork-safety clause of Requirement 5
(a true concurrent race serialises into a linear chain) needs real row locks and
is Postgres-gated like T-012's ConcurrentIssuanceTests — see the handoff.
"""
from xml.etree import ElementTree as ET

from django.test import TestCase

import compliance
from compliance.models import VerifactuRecord
from compliance.records import SF
from compliance.tests.factories import (
    ISSUER_NAME,
    ISSUER_NIF,
    issued_invoice,
)
from invoicing.tests.factories import make_series

FECHA_HORA = "2026-06-18T12:00:00+02:00"


def _find(elem, tag):
    return elem.find(f".//{{{SF}}}{tag}")


class ChainLinkageTests(TestCase):
    def setUp(self):
        # One series → sequential num_serie 1, 2 for the same issuer chain.
        self.series = make_series(prefix="")

    def _alta(self):
        invoice = issued_invoice(series=self.series, lines=[(1, "100.00", "21")])
        return compliance.generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )

    def test_second_record_links_to_first(self):
        rec1 = self._alta()
        rec2 = self._alta()

        self.assertEqual(rec2.previous_record_id, rec1.id)
        self.assertEqual(rec2.previous_huella, rec1.huella)

        root = ET.fromstring(rec2.xml)
        anterior = _find(root, "RegistroAnterior")
        self.assertIsNotNone(anterior)
        self.assertEqual(_find(anterior, "Huella").text, rec1.huella)
        self.assertIsNone(_find(root, "PrimerRegistro"))

    def test_chain_huellas_are_distinct_and_advance_head(self):
        rec1 = self._alta()
        rec2 = self._alta()
        self.assertNotEqual(rec1.huella, rec2.huella)
        from compliance.models import IssuerChain

        head = IssuerChain.objects.get(issuer_nif=ISSUER_NIF)
        self.assertEqual(head.last_huella, rec2.huella)


class AnnulmentTests(TestCase):
    def test_annulment_references_original_and_chains(self):
        series = make_series(prefix="")
        rec1 = compliance.generate_alta(
            issued_invoice(series=series, lines=[(1, "100.00", "21")]),
            issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME, fecha_hora=FECHA_HORA,
        )
        rec2 = compliance.generate_alta(
            issued_invoice(series=series, lines=[(1, "200.00", "21")]),
            issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME, fecha_hora=FECHA_HORA,
        )

        anul = compliance.generate_anulacion(rec1, fecha_hora=FECHA_HORA)

        self.assertEqual(anul.record_type, VerifactuRecord.ANULACION)
        # References the annulled invoice's identity (the original num_serie).
        root = ET.fromstring(anul.xml)
        self.assertEqual(_find(root, "NumSerieFacturaAnulada").text, rec1.num_serie)
        # Chained on the current tail (rec2), not a deletion.
        self.assertEqual(anul.previous_huella, rec2.huella)
        self.assertEqual(anul.previous_record_id, rec2.id)
        self.assertEqual(VerifactuRecord.objects.count(), 3)
