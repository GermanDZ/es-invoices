"""Requirement 2 — legal-field validation blocks malformed records (Q-1)."""
from django.core.exceptions import ValidationError
from django.test import TestCase

import compliance
from compliance.models import VerifactuRecord
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF, issued_invoice


class ValidationGateTests(TestCase):
    def test_missing_recipient_taxid_blocks_and_persists_nothing(self):
        invoice = issued_invoice()
        invoice.recipient_taxid = ""
        invoice.save()

        with self.assertRaises(ValidationError):
            compliance.generate_alta(
                invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME
            )
        self.assertEqual(VerifactuRecord.objects.count(), 0)

    def test_missing_issuer_nif_blocks(self):
        invoice = issued_invoice()
        with self.assertRaises(ValidationError):
            compliance.generate_alta(
                invoice, issuer_nif="", issuer_name=ISSUER_NAME
            )
        self.assertEqual(VerifactuRecord.objects.count(), 0)

    def test_unissued_invoice_blocks(self):
        from invoicing.tests.factories import make_invoice

        draft = make_invoice(lines=[(1, "100.00", "21")])  # not issued
        with self.assertRaises(ValidationError):
            compliance.generate_alta(
                draft, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME
            )
        self.assertEqual(VerifactuRecord.objects.count(), 0)
