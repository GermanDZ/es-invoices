"""Issuance UI view tests (T-022 Operation 5).

Covers the UC-001 browser path end to end: create → issue → PDF → send, plus the
two guard flows (no line items 2a; missing recipient field 6a), the IRPF-off
path, login-required, and owner-scoping. WeasyPrint PDF rendering is patched out
(its byte-for-byte output is `documents`' concern, tested in T-016); these tests
assert the *wiring* — that the views call the engine and surface its results.
"""
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from clients.models import Client
from compliance.models import VerifactuRecord
from invoicing.models import Invoice, Series

User = get_user_model()

_user_seq = 0


def make_user():
    global _user_seq
    _user_seq += 1
    return User.objects.create_user(username=f"autonomo{_user_seq}", password="pw")


def make_client(owner, *, client_type=Client.ClientType.B2B, tax_id="A58818501"):
    return Client.objects.create(
        owner=owner,
        fiscal_name="ACME SL",
        client_type=client_type,
        tax_id=tax_id,
        address="C/ Mayor 1",
    )


def issuance_payload(client, *, irpf="0", lines=((), ), filled=(("Servicio", "1", "100.00", "21"),)):
    """Build a POST dict for the issuance form + line-item formset.

    ``filled`` is a tuple of (description, quantity, unit_price, iva_rate) rows;
    remaining formset rows are left blank.
    """
    total_forms = max(3, len(filled))
    data = {
        "issuer_name": "Ana Autónoma",
        "issuer_nif": "12345678Z",
        "issuer_address": "C/ Sol 2",
        "issuer_email": "ana@example.com",
        "client": str(client.pk),
        "irpf_rate": irpf,
        "form-TOTAL_FORMS": str(total_forms),
        "form-INITIAL_FORMS": "0",
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    for i in range(total_forms):
        if i < len(filled):
            desc, qty, price, iva = filled[i]
        else:
            desc, qty, price, iva = "", "", "", "21"
        data[f"form-{i}-description"] = desc
        data[f"form-{i}-quantity"] = qty
        data[f"form-{i}-unit_price"] = price
        data[f"form-{i}-iva_rate"] = iva
    return data


class IssuanceFlowTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.recipient = make_client(self.user)

    def test_create_issues_invoice_and_assigns_gap_free_number(self):
        resp = self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        self.assertEqual(resp.status_code, 302)
        inv = Invoice.objects.get()
        self.assertTrue(inv.issued)
        self.assertEqual(inv.number, 1)
        self.assertEqual(inv.taxable_base, Decimal("100.00"))
        self.assertEqual(inv.iva_total, Decimal("21.00"))
        self.assertEqual(inv.irpf_retention, Decimal("0"))
        self.assertEqual(inv.client, self.recipient)
        self.assertEqual(resp["Location"], reverse("invoicing:detail", args=[inv.pk]))

        # A second issue gets the next consecutive number (gap-free).
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        self.assertEqual(
            sorted(Invoice.objects.values_list("number", flat=True)), [1, 2]
        )

    def test_create_and_detail_templates_render(self):
        # Authenticated GET renders the issuance form (formset + issuer fields)…
        resp = self.client.get(reverse("invoicing:create"))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "invoicing/invoice_form.html")
        # …and the detail page renders after issuance (totals + send form).
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        inv = Invoice.objects.get()
        detail = self.client.get(reverse("invoicing:detail", args=[inv.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertTemplateUsed(detail, "invoicing/invoice_detail.html")
        self.assertContains(detail, reverse("invoicing:pdf", args=[inv.pk]))

    def test_irpf_rate_is_applied(self):
        self.client.post(
            reverse("invoicing:create"), issuance_payload(self.recipient, irpf="15")
        )
        inv = Invoice.objects.get()
        self.assertEqual(inv.irpf_retention, Decimal("15.00"))  # 15% of 100
        self.assertEqual(inv.grand_total, Decimal("106.00"))    # 100 + 21 − 15

    def test_no_line_items_is_blocked_without_consuming_a_number(self):
        resp = self.client.post(
            reverse("invoicing:create"), issuance_payload(self.recipient, filled=())
        )
        self.assertEqual(resp.status_code, 200)            # re-rendered, not redirected
        self.assertEqual(Invoice.objects.count(), 0)
        series = Series.objects.get(owner=self.user)       # get-or-created, unused
        self.assertEqual(series.last_number, 0)

    def test_missing_recipient_taxid_is_blocked_without_consuming_a_number(self):
        # A B2C client with no tax-id yields a snapshot with blank recipient_taxid,
        # which issue_invoice rejects (alt-flow 6a).
        b2c = make_client(self.user, client_type=Client.ClientType.B2C, tax_id="")
        resp = self.client.post(reverse("invoicing:create"), issuance_payload(b2c))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Invoice.objects.count(), 0)
        series = Series.objects.get(owner=self.user)
        self.assertEqual(series.last_number, 0)

    @mock.patch("invoicing.views.render_invoice_pdf", return_value=b"%PDF-1.4 fake")
    def test_pdf_route_returns_application_pdf(self, _render):
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        inv = Invoice.objects.get()
        resp = self.client.get(reverse("invoicing:pdf", args=[inv.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertEqual(resp.content, b"%PDF-1.4 fake")
        _render.assert_called_once()

    @mock.patch("documents.services.render_invoice_pdf", return_value=b"%PDF-1.4 fake")
    def test_send_emails_pdf_and_marks_sent(self, _render):
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        inv = Invoice.objects.get()
        resp = self.client.post(
            reverse("invoicing:send", args=[inv.pk]), {"to_email": "dest@example.com"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["dest@example.com"])
        inv.refresh_from_db()
        self.assertIsNotNone(inv.sent_at)
        self.assertEqual(inv.status, "sent")


class VerifactuRecordGenerationTests(TestCase):
    """T-033 — invoice creation auto-generates an alta VerifactuRecord."""

    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.recipient = make_client(self.user)

    def test_create_generates_alta_record(self):
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        inv = Invoice.objects.get()
        self.assertEqual(
            inv.verifactu_records.filter(record_type=VerifactuRecord.ALTA).count(), 1
        )

    def test_detail_shows_submit_button_after_create(self):
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        inv = Invoice.objects.get()
        resp = self.client.get(reverse("invoicing:detail", args=[inv.pk]))
        self.assertTrue(resp.context["submission_can_submit"])

    def test_record_carries_issuer_from_form(self):
        self.client.post(reverse("invoicing:create"), issuance_payload(self.recipient))
        record = VerifactuRecord.objects.get(record_type=VerifactuRecord.ALTA)
        self.assertEqual(record.issuer_nif, "12345678Z")
        self.assertEqual(record.issuer_name, "Ana Autónoma")


class AuthAndScopingTests(TestCase):
    def test_create_requires_login(self):
        resp = self.client.get(reverse("invoicing:create"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_cross_owner_access_is_404(self):
        owner = make_user()
        recipient = make_client(owner)
        self.client.force_login(owner)
        self.client.post(reverse("invoicing:create"), issuance_payload(recipient))
        inv = Invoice.objects.get()

        intruder = make_user()
        self.client.force_login(intruder)
        for name in ("invoicing:detail", "invoicing:pdf"):
            self.assertEqual(self.client.get(reverse(name, args=[inv.pk])).status_code, 404)
        self.assertEqual(
            self.client.post(reverse("invoicing:send", args=[inv.pk])).status_code, 404
        )
