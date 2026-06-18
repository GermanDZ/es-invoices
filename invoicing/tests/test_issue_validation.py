"""Issuance validation + rollback tests (T-012 requirement 5)."""
from django.core.exceptions import ValidationError
from django.test import TestCase

from invoicing.models import Invoice
from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series


class IssueValidationTests(TestCase):
    def test_no_line_items_is_rejected_without_consuming_a_number(self):
        """Req 5 / alt-flow 2a: an invoice with no lines cannot be issued."""
        series = make_series()
        inv = make_invoice(series=series, lines=[])
        with self.assertRaises(ValidationError):
            issue_invoice(inv)
        inv.refresh_from_db()
        self.assertIsNone(inv.number)
        self.assertFalse(inv.issued)
        series.refresh_from_db()
        self.assertEqual(series.last_number, 0)        # high-water unchanged

    def test_missing_mandatory_field_rolls_back_and_number_not_consumed(self):
        """Req 5 / alt-flow 6a: a missing field blocks issuance; the next
        successful issue still gets the untouched next number."""
        series = make_series()
        bad = make_invoice(
            series=series, recipient_name="", lines=[(1, "100.00", 21)]
        )
        with self.assertRaises(ValidationError):
            issue_invoice(bad)
        series.refresh_from_db()
        self.assertEqual(series.last_number, 0)        # not consumed

        good = make_invoice(series=series, lines=[(1, "100.00", 21)])
        issue_invoice(good)
        self.assertEqual(good.number, 1)               # gets the untouched first number
        series.refresh_from_db()
        self.assertEqual(series.last_number, 1)

    def test_already_issued_invoice_cannot_be_reissued(self):
        series = make_series()
        inv = make_invoice(series=series, lines=[(1, "100.00", 21)])
        issue_invoice(inv)
        with self.assertRaises(ValidationError):
            issue_invoice(inv)
