"""AEAT submission UI view tests (T-023, UC-002).

Covers the browser submit path: the control's presence/absence on the invoice
detail page, each engine outcome surfaced (accepted / rejected / pending /
disabled), the already-accepted and no-record guards, owner-scoping (404), and
login-required. The submission engine runs for real with a *scripted gateway*
(patched into ``submission.services._default_gateway``) so attempt persistence and
the kill-switch are exercised end to end — the view itself never makes a network
call. The guard tests patch ``submission.views.submit_record`` to assert the engine
is not reached.
"""
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from submission.aeat_direct import SubmissionTransportError
from submission.gateway import SubmissionGateway, SubmissionOutcome, SubmissionStatus
from submission.models import SubmissionAttempt

from .factories import make_record

ENABLED = dict(AEAT_SUBMISSION_LIVE=True, AEAT_SUBMISSION_MAX_RETRIES=3, AEAT_ENV="preproduccion")


class _ScriptedGateway(SubmissionGateway):
    """Returns/raises a scripted sequence of outcomes, counting calls."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0

    def submit(self, record):
        self.calls += 1
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def _patch_gateway(gw):
    """Patch the engine's default gateway so the real submit_record uses ``gw``."""
    return mock.patch("submission.services._default_gateway", return_value=gw)


def _submit_url(record):
    return reverse("submission:submit", args=[record.invoice_id])


def _detail_url(record):
    return reverse("invoicing:detail", args=[record.invoice_id])


@override_settings(**ENABLED)
class OutcomeSurfacingTests(TestCase):
    """The four engine outcomes reach the user (Requirements 2, 3, 4, 5)."""

    def setUp(self):
        self.record = make_record()
        self.user = self.record.invoice.series.owner
        self.client.force_login(self.user)

    def test_accepted_persists_attempt_and_shows_receipt(self):
        gw = _ScriptedGateway([SubmissionOutcome(status=SubmissionStatus.ACCEPTED, csv="CSV-9")])
        with _patch_gateway(gw):
            resp = self.client.post(_submit_url(self.record), follow=True)
        self.assertEqual(gw.calls, 1)
        attempt = SubmissionAttempt.objects.get(record=self.record)
        self.assertEqual(attempt.status, SubmissionAttempt.ACCEPTED)
        self.assertContains(resp, "aceptado")
        self.assertContains(resp, "CSV-9")

    def test_rejected_surfaces_reason_and_keeps_control(self):
        gw = _ScriptedGateway(
            [SubmissionOutcome(status=SubmissionStatus.REJECTED, estado="Incorrecto",
                               aeat_code="3000", aeat_message="NIF no censado")]
        )
        with _patch_gateway(gw):
            resp = self.client.post(_submit_url(self.record), follow=True)
        self.assertEqual(SubmissionAttempt.objects.get(record=self.record).status,
                         SubmissionAttempt.REJECTED)
        self.assertContains(resp, "rechaz")
        self.assertContains(resp, "NIF no censado")
        # Rejection is correctable — the submit control remains available.
        self.assertContains(resp, _submit_url(self.record))

    def test_pending_surfaces_without_implying_success(self):
        gw = _ScriptedGateway([SubmissionTransportError("timeout")] * 4)  # 1 + 3 retries
        with _patch_gateway(gw):
            resp = self.client.post(_submit_url(self.record), follow=True)
        self.assertEqual(SubmissionAttempt.objects.get(record=self.record).status,
                         SubmissionAttempt.PENDING)
        self.assertContains(resp, "pendiente")


@override_settings(AEAT_SUBMISSION_LIVE=False)
class KillSwitchTests(TestCase):
    """Flag off → no attempt persisted, user told it is disabled (Requirement 5)."""

    def test_disabled_writes_no_attempt(self):
        record = make_record()
        self.client.force_login(record.invoice.series.owner)
        resp = self.client.post(_submit_url(record), follow=True)
        self.assertEqual(SubmissionAttempt.objects.count(), 0)
        self.assertContains(resp, "deshabilitado")


@override_settings(**ENABLED)
class DetailControlTests(TestCase):
    """The submit control appears only when submittable (Requirements 1, 7)."""

    def test_control_present_for_unsubmitted_record(self):
        record = make_record()
        self.client.force_login(record.invoice.series.owner)
        resp = self.client.get(_detail_url(record))
        self.assertContains(resp, _submit_url(record))
        self.assertContains(resp, "Enviar a la AEAT")

    def test_control_absent_once_accepted(self):
        record = make_record()
        SubmissionAttempt.objects.create(record=record, status=SubmissionAttempt.ACCEPTED, csv="CSV-1")
        self.client.force_login(record.invoice.series.owner)
        resp = self.client.get(_detail_url(record))
        self.assertNotContains(resp, _submit_url(record))
        self.assertContains(resp, "aceptado")


@override_settings(**ENABLED)
class GuardTests(TestCase):
    """No-record and already-accepted never reach the engine (Requirement 7)."""

    def test_already_accepted_does_not_resubmit(self):
        record = make_record()
        SubmissionAttempt.objects.create(record=record, status=SubmissionAttempt.ACCEPTED, csv="CSV-1")
        self.client.force_login(record.invoice.series.owner)
        with mock.patch("submission.views.submit_record") as engine:
            resp = self.client.post(_submit_url(record), follow=True)
        engine.assert_not_called()
        self.assertContains(resp, "ya fue aceptado")

    def test_no_record_reports_nothing_to_send(self):
        # An issued invoice with no alta record: build one via the invoicing
        # factory directly so verifactu_records is empty.
        from invoicing.tests.factories import make_series, make_user
        from compliance.tests.factories import issued_invoice
        owner = make_user()
        invoice = issued_invoice(series=make_series(owner=owner, prefix="NR"))
        self.client.force_login(owner)
        with mock.patch("submission.views.submit_record") as engine:
            resp = self.client.post(reverse("submission:submit", args=[invoice.pk]), follow=True)
        engine.assert_not_called()
        self.assertContains(resp, "registro Verifactu")

    def test_get_redirects_to_detail(self):
        record = make_record()
        self.client.force_login(record.invoice.series.owner)
        with mock.patch("submission.views.submit_record") as engine:
            resp = self.client.get(_submit_url(record))
        engine.assert_not_called()
        self.assertRedirects(resp, _detail_url(record))


@override_settings(**ENABLED)
class AccessControlTests(TestCase):
    """Owner-scoping (404) and login-required (Requirement 6)."""

    def test_cross_owner_submit_is_404(self):
        record = make_record()
        from invoicing.tests.factories import make_user
        intruder = make_user()
        self.client.force_login(intruder)
        with mock.patch("submission.views.submit_record") as engine:
            resp = self.client.post(_submit_url(record))
        self.assertEqual(resp.status_code, 404)
        engine.assert_not_called()

    def test_anonymous_is_redirected_to_login(self):
        record = make_record()
        resp = self.client.post(_submit_url(record))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)
