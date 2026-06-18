"""The AD-3 interface contract — Requirement 1 (interface conformance)."""
from django.test import TestCase

from submission.aeat_direct import AeatDirectAdapter
from submission.gateway import (
    SubmissionGateway,
    SubmissionOutcome,
    SubmissionStatus,
)


class GatewayContractTests(TestCase):
    def test_direct_adapter_is_a_submission_gateway(self):
        # A second adapter satisfying the same ABC would drop in unchanged (AD-3).
        adapter = AeatDirectAdapter(endpoint="https://example.test", transport=lambda *a, **k: "")
        self.assertIsInstance(adapter, SubmissionGateway)

    def test_gateway_cannot_be_instantiated_without_submit(self):
        class Incomplete(SubmissionGateway):
            pass  # no submit()

        with self.assertRaises(TypeError):
            Incomplete()

    def test_outcome_is_accepted_helper(self):
        ok = SubmissionOutcome(status=SubmissionStatus.ACCEPTED)
        rej = SubmissionOutcome(status=SubmissionStatus.REJECTED)
        self.assertTrue(ok.is_accepted)
        self.assertFalse(rej.is_accepted)
