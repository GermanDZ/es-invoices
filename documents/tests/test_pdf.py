"""T-016 — PDF rendering (Requirements 1, 2, 4, 5).

Text assertions extract the PDF's text layer with ``pypdf`` so they check what a
reader actually sees, not the HTML before layout.
"""
import io
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

import pypdf
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from documents.services import Issuer, build_qr_url, render_invoice_pdf
from invoicing.services import issue_invoice
from invoicing.tests.factories import make_invoice, make_series

ISSUER = Issuer(
    name="Ana Autónoma",
    nif="12345678Z",
    address="Calle Mayor 1, Madrid",
    email="ana@example.com",
)


def _pdf_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _issued(prefix="FRA-", irpf="0", lines=None):
    series = make_series(prefix=prefix)
    inv = make_invoice(
        series=series,
        irpf_rate=irpf,
        recipient_name="Cliente Ejemplo SL",
        recipient_taxid="B12345678",
        lines=lines or [(2, "50.00", "21"), (1, "100.00", "10")],
    )
    return issue_invoice(inv)


class RenderInvoicePdfTests(TestCase):
    def test_returns_a_valid_pdf(self):
        pdf = render_invoice_pdf(_issued(), issuer=ISSUER)
        self.assertTrue(pdf.startswith(b"%PDF-"))
        # pypdf parses it without error => structurally a PDF.
        self.assertGreaterEqual(len(pypdf.PdfReader(io.BytesIO(pdf)).pages), 1)

    def test_pdf_carries_mandatory_legal_fields(self):
        """Requirement 1: number, recipient NIF, line descriptions, grand total."""
        inv = _issued(lines=[(2, "50.00", "21")])  # base 100, iva 21 => total 121
        inv.items.create(
            description="Servicio de consultoría", quantity=Decimal("1"),
            unit_price=Decimal("0"), iva_rate=Decimal("21"),
        )
        pdf = render_invoice_pdf(inv, issuer=ISSUER)
        text = _pdf_text(pdf)
        self.assertIn(f"{inv.series.prefix}{inv.number}", text)  # series+number
        self.assertIn("B12345678", text)                        # recipient NIF
        self.assertIn("12345678Z", text)                        # issuer NIF
        self.assertIn("Servicio de consultoría", text)          # line description
        # grand total integer part (locale may format decimals with , or .)
        self.assertIn(str(inv.grand_total).split(".")[0], text)

    def test_pdf_carries_verifactu_legend(self):
        """Requirement 2: the VERI*FACTU legend text is on the page."""
        text = _pdf_text(render_invoice_pdf(_issued(), issuer=ISSUER))
        self.assertIn("VERI*FACTU", text)

    def test_qr_url_matches_persisted_verifactu_values(self):
        """Requirement 2: QR encodes NIF + persisted NumSerie/Fecha/Importe."""
        inv = _issued(prefix="A-", lines=[(2, "50.00", "21")])
        url = build_qr_url(inv, ISSUER)
        q = parse_qs(urlparse(url).query)
        self.assertEqual(q["nif"], [ISSUER.nif])
        self.assertEqual(q["numserie"], [f"{inv.series.prefix}{inv.number}"])
        self.assertEqual(q["fecha"], [inv.issue_date.strftime("%d-%m-%Y")])
        # Verifactu importe = base + iva (IRPF not subtracted).
        expected = f"{inv.taxable_base + inv.iva_total:.2f}"
        self.assertEqual(q["importe"], [expected])

    @override_settings(VERIFACTU_QR_BASE_URL="https://www2.agenciatributaria.gob.es/x/ValidarQR")
    def test_qr_base_url_is_config_driven(self):
        url = build_qr_url(_issued(), issuer=ISSUER)
        self.assertTrue(url.startswith("https://www2.agenciatributaria.gob.es/x/ValidarQR?"))

    def test_draft_invoice_is_rejected(self):
        """Requirement 4: a not-yet-issued invoice cannot be rendered."""
        draft = make_invoice(lines=[(1, "10.00", "21")])
        self.assertFalse(draft.issued)
        with self.assertRaises(ValidationError):
            render_invoice_pdf(draft, issuer=ISSUER)

    def test_render_does_not_mutate_invoice_or_series(self):
        """Requirement 5: rendering is read-only on invoice, items, series."""
        inv = _issued(lines=[(3, "10.00", "21")])
        inv.series.refresh_from_db()  # drop the stale in-memory series from issuance
        before = (
            inv.number, inv.issue_date, inv.grand_total,
            inv.taxable_base, inv.iva_total,
        )
        items_before = list(inv.items.values_list("id", "description", "unit_price"))
        last_number_before = inv.series.last_number

        render_invoice_pdf(inv, issuer=ISSUER)

        inv.refresh_from_db()
        inv.series.refresh_from_db()
        after = (
            inv.number, inv.issue_date, inv.grand_total,
            inv.taxable_base, inv.iva_total,
        )
        self.assertEqual(before, after)
        self.assertEqual(items_before,
                         list(inv.items.values_list("id", "description", "unit_price")))
        self.assertEqual(last_number_before, inv.series.last_number)
