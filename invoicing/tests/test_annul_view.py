"""T-024 — annulment UI view tests (UC-005).

Covers the browser path that drives the shipped ``annul_invoice`` engine (T-017):
the step-2 warning/confirm page (Req 5), the happy path that marks the invoice
annulled (Req 6), the UC-005 2b refusal surfaced as a message rather than a 500
(Req 7), and owner-scoping (Req 8). Runs with ``AEAT_SUBMISSION_LIVE`` off → DISABLED
outcome, so no live AEAT call is made (the engine still marks annulled on DISABLED).
"""
from django.test import TestCase
from django.urls import reverse

import compliance
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF
from invoicing.models import Invoice
from invoicing.tests.factories import make_invoice, make_series, make_user

FECHA_HORA = "2026-06-20T12:00:00+02:00"


def _issued_original(owner, lines=((1, "100.00", "21"),)):
    from compliance.tests.factories import issued_invoice

    invoice = issued_invoice(series=make_series(owner=owner), lines=list(lines))
    compliance.generate_alta(
        invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME, fecha_hora=FECHA_HORA
    )
    return invoice


class AnnulViewTests(TestCase):
    def setUp(self):
        self.owner = make_user()
        self.client.force_login(self.owner)
        self.invoice = _issued_original(self.owner)

    def test_detail_shows_anular_link(self):
        resp = self.client.get(reverse("invoicing:detail", args=[self.invoice.pk]))
        self.assertContains(resp, reverse("invoicing:annul", args=[self.invoice.pk]))

    def test_get_renders_warning_and_confirm(self):
        # Requirement 5 — the step-2 warning page is shown before any action.
        resp = self.client.get(reverse("invoicing:annul", args=[self.invoice.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "error")  # warns it is only for records sent in error
        self.assertContains(resp, "Confirmar")
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.annulled)  # GET makes no change

    def test_post_marks_annulled_and_redirects(self):
        # Requirement 6 — confirm drives the engine; invoice ends annulled.
        resp = self.client.post(reverse("invoicing:annul", args=[self.invoice.pk]))
        self.assertRedirects(resp, reverse("invoicing:detail", args=[self.invoice.pk]))
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.annulled)

    def test_post_on_corrected_invoice_is_refused_as_message_not_500(self):
        # Requirement 7 — UC-005 2b: an invoice carrying a rectificativa cannot be
        # annulled; the engine ValidationError is surfaced, invoice stays not-annulled.
        rect = make_invoice(
            series=make_series(owner=self.owner, prefix="R"),
            lines=[(1, "80.00", "21")],
        )
        from invoicing.services import issue_rectificativa

        issue_rectificativa(
            rect, self.invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self.invoice.refresh_from_db()
        resp = self.client.post(reverse("invoicing:annul", args=[self.invoice.pk]))
        self.assertRedirects(resp, reverse("invoicing:detail", args=[self.invoice.pk]))
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.annulled)

    def test_cross_owner_is_404(self):
        # Requirement 8 — another owner's invoice is a 404 on GET and POST.
        other = make_user()
        self.client.force_login(other)
        url = reverse("invoicing:annul", args=[self.invoice.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.annulled)
