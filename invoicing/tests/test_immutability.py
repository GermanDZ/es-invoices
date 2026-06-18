"""Issued-invoice immutability + persisted totals (T-012 requirement 6)."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series


class ImmutabilityTests(TestCase):
    def _issued(self):
        series = make_series()
        inv = make_invoice(
            series=series,
            recipient_name="Cliente SL",
            recipient_taxid="B12345678",
            lines=[(1, "100.00", 21)],
        )
        issue_invoice(inv)
        return inv

    def test_number_is_immutable_once_issued(self):
        inv = self._issued()
        inv.number = 999
        with self.assertRaises(ValidationError):
            inv.save()

    def test_issue_date_is_immutable_once_issued(self):
        inv = self._issued()
        inv.issue_date = inv.issue_date.replace(year=inv.issue_date.year - 1)
        with self.assertRaises(ValidationError):
            inv.save()

    def test_snapshot_and_totals_persist_and_are_readable(self):
        inv = self._issued()
        inv.refresh_from_db()
        self.assertEqual(inv.recipient_name, "Cliente SL")
        self.assertEqual(inv.recipient_taxid, "B12345678")
        self.assertEqual(inv.taxable_base, Decimal("100.00"))
        self.assertEqual(inv.iva_total, Decimal("21.00"))
        self.assertEqual(inv.grand_total, Decimal("121.00"))
