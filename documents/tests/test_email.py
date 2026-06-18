"""T-016 — send by email (Requirements 3, 4).

Uses Django's in-memory (locmem) email backend so the outbox is inspectable and
nothing leaves the process.
"""
from unittest import mock

from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from documents.services import Issuer, send_invoice_email
from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series

ISSUER = Issuer(name="Ana Autónoma", nif="12345678Z", email="ana@example.com")


def _issued():
    series = make_series(prefix="FRA-")
    inv = make_invoice(
        series=series,
        recipient_name="Cliente Ejemplo SL",
        recipient_taxid="B12345678",
        lines=[(2, "50.00", "21")],
    )
    return issue_invoice(inv)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendInvoiceEmailTests(TestCase):
    def test_sends_one_message_with_pdf_attachment(self):
        """Requirement 3: one message, addressed to recipient, one PDF attached."""
        inv = _issued()
        sent = send_invoice_email(inv, issuer=ISSUER, to_email="cliente@example.com")

        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["cliente@example.com"])
        self.assertIn(f"{inv.series.prefix}{inv.number}", msg.subject)
        self.assertEqual(len(msg.attachments), 1)
        filename, content, mimetype = msg.attachments[0]
        self.assertTrue(filename.endswith(".pdf"))
        self.assertEqual(mimetype, "application/pdf")
        self.assertTrue(bytes(content).startswith(b"%PDF-"))

    def test_successful_send_emits_instrumentation_log(self):
        """Success-measure instrumentation: one invoice_email_sent record, NumSerie
        only, no recipient PII."""
        inv = _issued()
        with self.assertLogs("documents", level="INFO") as cm:
            send_invoice_email(inv, issuer=ISSUER, to_email="cliente@example.com")
        line = "\n".join(cm.output)
        self.assertIn("invoice_email_sent", line)
        self.assertIn(f"{inv.series.prefix}{inv.number}", line)
        self.assertNotIn("cliente@example.com", line)  # no PII in logs

    def test_from_email_defaults_to_issuer_or_settings(self):
        inv = _issued()
        send_invoice_email(inv, issuer=ISSUER, to_email="cliente@example.com")
        self.assertEqual(mail.outbox[0].from_email, "ana@example.com")

    def test_missing_recipient_raises_and_sends_nothing(self):
        """No client email on file and no to_email => refuse, send nothing."""
        inv = _issued()
        with self.assertRaises(ValidationError):
            send_invoice_email(inv, issuer=ISSUER)
        self.assertEqual(len(mail.outbox), 0)

    def test_draft_invoice_is_rejected_and_sends_nothing(self):
        """Requirement 4: a draft invoice cannot be sent."""
        draft = make_invoice(lines=[(1, "10.00", "21")])
        with self.assertRaises(ValidationError):
            send_invoice_email(draft, issuer=ISSUER, to_email="cliente@example.com")
        self.assertEqual(len(mail.outbox), 0)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SendPersistsStatusTests(TestCase):
    """T-018 Requirements 3, 4: a confirmed send advances the invoice to 'sent';
    a zero/failed send leaves it untouched."""

    def test_successful_send_marks_invoice_sent(self):
        inv = _issued()
        self.assertEqual(inv.status, "issued")
        send_invoice_email(inv, issuer=ISSUER, to_email="cliente@example.com")
        inv.refresh_from_db()
        self.assertIsNotNone(inv.sent_at)
        self.assertEqual(inv.status, "sent")

    def test_zero_send_leaves_invoice_unsent(self):
        """A send returning 0 (nothing delivered) must not stamp sent_at."""
        inv = _issued()
        with mock.patch("documents.services.EmailMessage.send", return_value=0):
            sent = send_invoice_email(inv, issuer=ISSUER, to_email="cliente@example.com")
        self.assertEqual(sent, 0)
        inv.refresh_from_db()
        self.assertIsNone(inv.sent_at)
        self.assertEqual(inv.status, "issued")
