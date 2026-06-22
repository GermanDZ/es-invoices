"""End-to-end smoke tests — happy path from login to PDF download.

These tests verify the core user journey works as an integrated whole:

  1. Dev auto-login (/dev/login/)
  2. Create a B2B client
  3. Issue an invoice with one line item
  4. View the invoice detail page
  5. Download the invoice PDF

They use override_settings(ROOT_URLCONF="devtools.tests.smoke_urls") so all
product routes are available regardless of the DEBUG flag that the test runner
forces to False.

These are smoke tests — they check that the main path doesn't blow up, not that
every edge case is handled. Per-feature unit tests live in each app's tests/.
"""
from django.test import TestCase, override_settings
from django.urls import reverse

from clients.models import Client
from devtools.owner import get_or_create_dev_owner
from invoicing.models import Invoice


SMOKE_URLCONF = "devtools.tests.smoke_urls"

# Minimal issuer data used in every invoice create POST.
_ISSUER = {
    "issuer_name": "Autónomo Prueba",
    "issuer_nif": "12345678Z",
    "issuer_address": "Calle Mayor 1, Madrid",
    "issuer_email": "prueba@example.com",
}

# Valid formset management form for LineItemFormSet (extra=3, no initial forms).
_FORMSET_MGMT = {
    "form-TOTAL_FORMS": "3",
    "form-INITIAL_FORMS": "0",
    "form-MIN_NUM_FORMS": "0",
    "form-MAX_NUM_FORMS": "1000",
}

# One filled line item at index 0 (description required to count as filled).
_LINE_ITEM_0 = {
    "form-0-description": "Consultoría técnica",
    "form-0-quantity": "1",
    "form-0-unit_price": "1000.00",
    "form-0-iva_rate": "21",
}

# Empty rows at indices 1 and 2 (no description → skipped by the view).
_LINE_ITEM_1 = {"form-1-description": "", "form-1-quantity": "", "form-1-unit_price": "", "form-1-iva_rate": "21"}
_LINE_ITEM_2 = {"form-2-description": "", "form-2-quantity": "", "form-2-unit_price": "", "form-2-iva_rate": "21"}


def _invoice_post_data(client_pk):
    """Build the full POST payload for the invoice create view."""
    return {
        **_ISSUER,
        "client": str(client_pk),
        "irpf_rate": "0",
        **_FORMSET_MGMT,
        **_LINE_ITEM_0,
        **_LINE_ITEM_1,
        **_LINE_ITEM_2,
    }


@override_settings(DEBUG=True, ROOT_URLCONF=SMOKE_URLCONF)
class SmokeDevLoginTest(TestCase):
    """Dev-login shortcut authenticates and lands on the client list."""

    def test_dev_login_authenticates(self):
        resp = self.client.get(reverse("devtools:login"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)


@override_settings(DEBUG=True, ROOT_URLCONF=SMOKE_URLCONF)
class SmokeClientCreateTest(TestCase):
    """Client creation — B2B with a valid CIF."""

    def setUp(self):
        self.user, _ = get_or_create_dev_owner()
        self.client.force_login(self.user)

    def test_create_b2b_client_succeeds(self):
        resp = self.client.post(
            reverse("clients:create"),
            {
                "fiscal_name": "ACME SL",
                "client_type": "B2B",
                "tax_id": "A58818501",
                "address": "Calle Gran Vía 1, Madrid",
                "email": "acme@example.com",
            },
        )
        self.assertEqual(resp.status_code, 302, f"Create client failed: {resp.content[:300]}")
        self.assertEqual(Client.objects.filter(owner=self.user, fiscal_name="ACME SL").count(), 1)

    def test_client_list_visible(self):
        resp = self.client.get(reverse("clients:list"))
        self.assertEqual(resp.status_code, 200)


@override_settings(DEBUG=True, ROOT_URLCONF=SMOKE_URLCONF)
class SmokeInvoiceFlowTest(TestCase):
    """Full invoice flow: create client → issue invoice → detail → PDF."""

    def setUp(self):
        self.user, _ = get_or_create_dev_owner()
        self.client.force_login(self.user)

        # Create the client that will be the invoice recipient.
        self.recipient = Client.objects.create(
            owner=self.user,
            fiscal_name="ACME SL",
            client_type=Client.ClientType.B2B,
            tax_id="A58818501",
            address="Calle Gran Vía 1, Madrid",
        )

    def test_issue_invoice_assigns_number(self):
        resp = self.client.post(
            reverse("invoicing:create"),
            _invoice_post_data(self.recipient.pk),
        )
        self.assertEqual(resp.status_code, 302, f"Invoice create failed: {resp.content[:400]}")

        invoice = Invoice.objects.filter(series__owner=self.user).first()
        self.assertIsNotNone(invoice, "No invoice was created")
        self.assertTrue(invoice.issued, "Invoice was not issued")
        self.assertEqual(invoice.number, 1, "First invoice should have number 1")

    def test_invoice_detail_page_renders(self):
        self.client.post(
            reverse("invoicing:create"),
            _invoice_post_data(self.recipient.pk),
        )
        invoice = Invoice.objects.filter(series__owner=self.user).first()
        resp = self.client.get(reverse("invoicing:detail", kwargs={"pk": invoice.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_invoice_pdf_download(self):
        self.client.post(
            reverse("invoicing:create"),
            _invoice_post_data(self.recipient.pk),
        )
        invoice = Invoice.objects.filter(series__owner=self.user).first()

        # The session issuer key is set by the create view; the PDF view reads it.
        resp = self.client.get(reverse("invoicing:pdf", kwargs={"pk": invoice.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        # PDF magic bytes
        self.assertTrue(resp.content.startswith(b"%PDF-"), "Response is not a valid PDF")

    def test_invoice_totals_are_correct(self):
        self.client.post(
            reverse("invoicing:create"),
            _invoice_post_data(self.recipient.pk),
        )
        invoice = Invoice.objects.filter(series__owner=self.user).first()
        totals = invoice.compute_totals()
        # 1 × 1000 @ 21% IVA, 0% IRPF
        self.assertEqual(totals.taxable_base, 1000)
        self.assertEqual(totals.iva_total, 210)
        self.assertEqual(totals.grand_total, 1210)

    def test_sequential_numbering_across_invoices(self):
        for _ in range(3):
            self.client.post(
                reverse("invoicing:create"),
                _invoice_post_data(self.recipient.pk),
            )
        numbers = sorted(
            Invoice.objects.filter(series__owner=self.user).values_list("number", flat=True)
        )
        self.assertEqual(numbers, [1, 2, 3], "Invoice numbers must be sequential with no gaps")
