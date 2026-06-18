"""T-018 — basic invoice status tracking (issued / sent), S-6.

Covers the derived ``Invoice.status`` property and ``mark_sent()`` stamping,
including the interaction with the issued-identity immutability guard (T-012).
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series


def _issued():
    inv = make_invoice(series=make_series(prefix="FRA-"), lines=[(1, "100.00", 21)])
    return issue_invoice(inv)


class StatusPropertyTests(TestCase):
    def test_draft_invoice_reports_draft(self):
        """Requirement 2: not issued => 'draft', sent_at is None (Requirement 1)."""
        draft = make_invoice(lines=[(1, "10.00", 21)])
        self.assertIsNone(draft.sent_at)
        self.assertEqual(draft.status, "draft")

    def test_issued_unsent_invoice_reports_issued(self):
        """Requirement 1 & 2: issued but never sent => sent_at None, status 'issued'."""
        inv = _issued()
        inv.refresh_from_db()
        self.assertIsNone(inv.sent_at)
        self.assertEqual(inv.status, "issued")

    def test_sent_invoice_reports_sent(self):
        """Requirement 2: once sent_at is set => status 'sent'."""
        inv = _issued()
        inv.mark_sent()
        inv.refresh_from_db()
        self.assertIsNotNone(inv.sent_at)
        self.assertEqual(inv.status, "sent")


class MarkSentTests(TestCase):
    def test_mark_sent_does_not_trip_immutability_guard(self):
        """Requirement 5: stamping sent_at on an issued invoice is allowed
        (sent_at is not an identity field)."""
        inv = _issued()
        inv.mark_sent()  # must not raise ValidationError
        inv.refresh_from_db()
        self.assertEqual(inv.status, "sent")

    def test_resend_advances_sent_at_to_later_time(self):
        """Requirement 6: a second send updates sent_at to the later time."""
        inv = _issued()
        t1 = timezone.now() - timedelta(hours=1)
        t2 = timezone.now()
        inv.mark_sent(when=t1)
        inv.mark_sent(when=t2)
        inv.refresh_from_db()
        self.assertEqual(inv.sent_at, t2)
