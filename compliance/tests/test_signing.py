"""Requirement 6 — XAdES-enveloped signature verifies, and fails on tamper."""
import base64
import os
from decimal import Decimal

from django.test import SimpleTestCase, TestCase, override_settings

from compliance import records, signing
from compliance.models import VerifactuRecord
from compliance.services import generate_alta
from compliance.tests.factories import (
    ISSUER_NAME,
    ISSUER_NIF,
    fixture_cert_material,
    issued_invoice,
)
from invoicing.calc import InvoiceTotals, RateGroup

FECHA_HORA = "2026-06-18T12:00:00+02:00"


def _alta_element():
    totals = InvoiceTotals(
        taxable_base=Decimal("100.00"),
        iva_total=Decimal("21.00"),
        irpf_retention=Decimal("0"),
        grand_total=Decimal("121.00"),
        groups=(RateGroup(Decimal("21"), Decimal("100.00"), Decimal("21.00")),),
    )
    element, *_ = records.build_registro_alta(
        issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME, num_serie="1",
        fecha_exp="18-06-2026", fecha_hora=FECHA_HORA, totals=totals,
        recipient_name="Cliente SL", recipient_taxid="A82037292",
    )
    return element


class SignatureTests(SimpleTestCase):
    def test_signature_verifies_against_certificate(self):
        cert_material, cert_pem = fixture_cert_material()
        signed = signing.sign_record(_alta_element(), cert_material)
        self.assertIn("Signature", signed)
        # Raises if invalid; returns a non-empty result on success.
        result = signing.verify_record(signed, cert_pem)
        self.assertTrue(result)

    def test_tampered_content_fails_verification(self):
        cert_material, cert_pem = fixture_cert_material()
        signed = signing.sign_record(_alta_element(), cert_material)
        tampered = signed.replace("Cliente SL", "Otro Cliente", 1)
        self.assertNotEqual(tampered, signed)
        with self.assertRaises(Exception):
            signing.verify_record(tampered, cert_pem)


@override_settings(CERT_ENCRYPTION_KEY=base64.b64encode(os.urandom(32)).decode())
class SignedGenerationTests(TestCase):
    def test_generate_alta_signs_via_certificate_store(self):
        from certificates.services import store_certificate

        invoice = issued_invoice(lines=[(1, "100.00", "21")])
        cert_material, cert_pem = fixture_cert_material()
        owner = invoice.series.owner
        store_certificate(
            owner,
            p12_bytes=cert_material.p12_bytes,
            passphrase=cert_material.passphrase,
            subject=cert_material.subject,
            not_after=cert_material.not_after,
        )

        record = generate_alta(
            invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA, signer=signing.signer_for_user(owner),
        )
        self.assertTrue(record.signed)
        self.assertEqual(record.record_type, VerifactuRecord.ALTA)
        self.assertIn("Signature", record.xml)
        self.assertTrue(signing.verify_record(record.xml, cert_pem))
