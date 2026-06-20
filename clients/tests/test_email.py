"""T-025 R5 (form half) — the optional ``Client.email`` field.

``email`` is optional for both B2B and B2C: validated when present, accepted when
blank, never required. The recipient-resolution half (``send_invoice_email`` using
the saved address) lives in ``documents/tests/test_email.py``.
"""
from django.test import TestCase

from clients.forms import ClientForm
from clients.tests.factories import make_user


def _data(**over):
    base = {
        "fiscal_name": "ACME SL",
        "client_type": "B2B",
        "tax_id": "A58818501",  # valid CIF
        "address": "C/ Mayor 1",
        "email": "",
    }
    base.update(over)
    return base


class ClientEmailFormTests(TestCase):
    def test_valid_email_persists(self):
        owner = make_user()
        form = ClientForm(_data(email="cliente@example.com"))
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save(commit=False)
        obj.owner = owner
        obj.save()
        obj.refresh_from_db()
        self.assertEqual(obj.email, "cliente@example.com")

    def test_invalid_email_is_rejected_with_field_error(self):
        form = ClientForm(_data(email="not-an-email"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_empty_email_is_allowed(self):
        form = ClientForm(_data(email=""))
        self.assertTrue(form.is_valid(), form.errors)
