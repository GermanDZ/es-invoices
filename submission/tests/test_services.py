"""Orchestration policy — Requirements 4, 5, 6 (flag, retry/pending, persistence)."""
from django.test import TestCase, override_settings

from submission.aeat_direct import SubmissionTransportError
from submission.gateway import SubmissionGateway, SubmissionOutcome, SubmissionStatus
from submission.models import SubmissionAttempt
from submission.services import submit_record

from .factories import make_record


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


ENABLED = dict(AEAT_SUBMISSION_ENABLED=True, AEAT_SUBMISSION_MAX_RETRIES=3, AEAT_ENV="preproduccion")


@override_settings(AEAT_SUBMISSION_ENABLED=False)
class FlagOffTests(TestCase):
    def test_disabled_short_circuits_and_writes_no_attempt(self):
        record = make_record()
        gw = _ScriptedGateway([SubmissionOutcome(status=SubmissionStatus.ACCEPTED)])
        outcome = submit_record(record, gateway=gw)
        self.assertIs(outcome.status, SubmissionStatus.DISABLED)
        self.assertEqual(gw.calls, 0, "no gateway call when the flag is off")
        self.assertEqual(SubmissionAttempt.objects.count(), 0)


@override_settings(**ENABLED)
class OrchestrationTests(TestCase):
    def test_accepted_persists_attempt_and_leaves_record_untouched(self):
        record = make_record()
        before_xml = record.xml
        gw = _ScriptedGateway(
            [SubmissionOutcome(status=SubmissionStatus.ACCEPTED, estado="Correcto", csv="CSV-9")]
        )
        outcome = submit_record(record, gateway=gw)

        self.assertIs(outcome.status, SubmissionStatus.ACCEPTED)
        attempt = SubmissionAttempt.objects.get(record=record)
        self.assertEqual(attempt.status, "accepted")
        self.assertEqual(attempt.csv, "CSV-9")
        self.assertEqual(attempt.retries, 0)
        record.refresh_from_db()
        self.assertEqual(record.xml, before_xml)  # record never mutated

    def test_rejection_is_not_retried(self):
        record = make_record()
        gw = _ScriptedGateway(
            [SubmissionOutcome(status=SubmissionStatus.REJECTED, estado="Incorrecto", aeat_code="3000")]
        )
        outcome = submit_record(record, gateway=gw)

        self.assertIs(outcome.status, SubmissionStatus.REJECTED)
        self.assertEqual(gw.calls, 1, "a business rejection must not retry")
        self.assertEqual(SubmissionAttempt.objects.get(record=record).status, "rejected")

    def test_persistent_transport_failure_degrades_to_pending(self):
        record = make_record()
        gw = _ScriptedGateway([SubmissionTransportError("timeout")] * 4)  # 1 + 3 retries
        outcome = submit_record(record, gateway=gw)

        self.assertIs(outcome.status, SubmissionStatus.PENDING)
        self.assertEqual(gw.calls, 4)
        attempt = SubmissionAttempt.objects.get(record=record)
        self.assertEqual(attempt.status, "pending")
        self.assertEqual(attempt.retries, 3)

    def test_transient_failure_then_acceptance_records_retry_count(self):
        record = make_record()
        gw = _ScriptedGateway(
            [
                SubmissionTransportError("reset"),
                SubmissionOutcome(status=SubmissionStatus.ACCEPTED, estado="Correcto", csv="CSV-R"),
            ]
        )
        outcome = submit_record(record, gateway=gw)

        self.assertIs(outcome.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(gw.calls, 2)
        self.assertEqual(SubmissionAttempt.objects.get(record=record).retries, 1)
