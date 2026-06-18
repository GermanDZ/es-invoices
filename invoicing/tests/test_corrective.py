"""T-017 — corrective / cancellation flows (requirements 1, 3, 4, 5, 6).

Covers the Invoice-side orchestration: rectificativa issuance (UC-004) and
annulment of an erroneous record (UC-005), the corrected/annulled gating on the
submission outcome, the annulment guardrail, and the no-number-burn / post-issue
mutation invariants. Submission is exercised via the AD-3 gateway seam — disabled
by default (kill-switch off → DISABLED) and a scripted gateway for the
accepted/rejected paths.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

import compliance
from compliance.models import VerifactuRecord
from compliance.tests.factories import ISSUER_NAME, ISSUER_NIF, issued_invoice
from invoicing.models import Invoice
from invoicing.services import annul_invoice, issue_rectificativa
from invoicing.tests.factories import make_invoice, make_series
from submission.gateway import SubmissionGateway, SubmissionOutcome, SubmissionStatus

FECHA_HORA = "2026-06-18T12:00:00+02:00"
ENABLED = dict(AEAT_SUBMISSION_LIVE=True, AEAT_SUBMISSION_MAX_RETRIES=3,
               AEAT_ENV="preproduccion")


class _ScriptedGateway(SubmissionGateway):
    """Returns a fixed outcome for every submit (T-014 test pattern)."""

    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = 0

    def submit(self, record):
        self.calls += 1
        return self.outcome


def _alta(invoice):
    return compliance.generate_alta(
        invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
        fecha_hora=FECHA_HORA,
    )


class RectificativaIssuanceTests(TestCase):
    """Requirement 1 + 3 — issuance, linkage, outcome gating."""

    def setUp(self):
        self.original = issued_invoice(lines=[(1, "100.00", "21")])
        _alta(self.original)
        self.rect_series = make_series(
            owner=self.original.series.owner, prefix="REC"
        )

    def _draft_rectificativa(self):
        return make_invoice(series=self.rect_series, lines=[(1, "80.00", "21")])

    def test_disabled_issues_numbers_links_and_recomputes_totals(self):
        # Kill-switch off → DISABLED outcome still marks corrected (req 3).
        rect = self._draft_rectificativa()
        out_rect, record, outcome = issue_rectificativa(
            rect, self.original, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self.assertIs(outcome.status, SubmissionStatus.DISABLED)
        # Requirement 1: issued, gap-free in the rectificativa series, references
        # the original (via the reverse manager), totals recomputed from own lines.
        rect.refresh_from_db()
        self.rect_series.refresh_from_db()
        self.assertTrue(rect.issued)
        self.assertEqual(rect.number, self.rect_series.last_number)
        self.assertEqual(rect.taxable_base, Decimal("80.00"))
        self.assertEqual(record.tipo_factura, "R1")
        # Requirement 3: original linked + marked corrected.
        self.original.refresh_from_db()
        self.assertEqual(self.original.corrected_by_id, rect.id)
        # Requirement 1: the rectificativa references the original via the reverse
        # manager (`corrects` = invoices this rectificativa corrects).
        self.assertEqual(rect.corrects.get().id, self.original.id)

    @override_settings(**ENABLED)
    def test_accepted_marks_original_corrected(self):
        rect = self._draft_rectificativa()
        gw = _ScriptedGateway(
            SubmissionOutcome(status=SubmissionStatus.ACCEPTED, estado="Correcto")
        )
        issue_rectificativa(
            rect, self.original, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA, gateway=gw,
        )
        self.original.refresh_from_db()
        self.assertEqual(self.original.corrected_by_id, rect.id)
        self.assertEqual(gw.calls, 1)

    @override_settings(**ENABLED)
    def test_rejected_leaves_original_uncorrected(self):
        rect = self._draft_rectificativa()
        gw = _ScriptedGateway(
            SubmissionOutcome(status=SubmissionStatus.REJECTED, estado="Incorrecto",
                              aeat_code="3000")
        )
        issue_rectificativa(
            rect, self.original, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA, gateway=gw,
        )
        self.original.refresh_from_db()
        self.assertIsNone(self.original.corrected_by_id)
        # The rectificativa invoice + record still exist (the rejection is the
        # report's verdict, not a rollback of issuance) — UC-004 9a.
        self.assertTrue(Invoice.objects.filter(pk=rect.pk, issued=True).exists())


class AnnulmentTests(TestCase):
    """Requirement 4 + 5 — annulment + guardrail."""

    def setUp(self):
        self.invoice = issued_invoice(lines=[(1, "100.00", "21")])
        _alta(self.invoice)

    def test_annulment_creates_chained_record_marks_annulled_no_new_invoice(self):
        before = Invoice.objects.count()
        record, outcome = annul_invoice(
            self.invoice, fecha_hora=FECHA_HORA,
        )
        self.assertIs(outcome.status, SubmissionStatus.DISABLED)
        self.assertEqual(record.record_type, VerifactuRecord.ANULACION)
        self.assertEqual(record.previous_huella,
                         self.invoice.verifactu_records.get(
                             record_type=VerifactuRecord.ALTA).huella)
        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.annulled)
        self.assertEqual(Invoice.objects.count(), before, "no new Invoice")

    @override_settings(**ENABLED)
    def test_rejected_annulment_leaves_invoice_not_annulled(self):
        gw = _ScriptedGateway(
            SubmissionOutcome(status=SubmissionStatus.REJECTED, estado="Incorrecto")
        )
        annul_invoice(self.invoice, fecha_hora=FECHA_HORA, gateway=gw)
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.annulled)

    def test_guardrail_refuses_annulment_when_rectificativa_exists(self):
        # A corrected (real-sale) invoice must not be annulled (UC-005 2b).
        rect_series = make_series(owner=self.invoice.series.owner, prefix="REC")
        rect = make_invoice(series=rect_series, lines=[(1, "80.00", "21")])
        issue_rectificativa(
            rect, self.invoice, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
            fecha_hora=FECHA_HORA,
        )
        self.invoice.refresh_from_db()
        with self.assertRaises(ValidationError):
            annul_invoice(self.invoice, fecha_hora=FECHA_HORA)
        self.assertFalse(
            self.invoice.verifactu_records.filter(
                record_type=VerifactuRecord.ANULACION).exists()
        )


class InvariantTests(TestCase):
    """Requirement 6 + Operation 1 — no number burn, post-issue mutation allowed."""

    def test_rectificativa_missing_lines_does_not_consume_a_number(self):
        original = issued_invoice(lines=[(1, "100.00", "21")])
        _alta(original)
        rect_series = make_series(owner=original.series.owner, prefix="REC")
        empty = make_invoice(series=rect_series, lines=[])  # no line items
        with self.assertRaises(ValidationError):
            issue_rectificativa(
                empty, original, issuer_nif=ISSUER_NIF, issuer_name=ISSUER_NAME,
                fecha_hora=FECHA_HORA,
            )
        rect_series.refresh_from_db()
        self.assertEqual(rect_series.last_number, 0, "series number not consumed")
        original.refresh_from_db()
        self.assertIsNone(original.corrected_by_id)

    def test_corrected_and_annulled_are_mutable_after_issue(self):
        # Operation 1 acceptance: the two new fields are NOT in the immutable set.
        inv = issued_invoice(lines=[(1, "100.00", "21")])
        inv.annulled = True
        inv.save()  # must not raise (series/number/issue_date unchanged)
        inv.refresh_from_db()
        self.assertTrue(inv.annulled)
