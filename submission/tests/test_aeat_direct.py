"""Adapter transport + parsing — Requirements 2 & 3 (and least-privilege)."""
from django.test import TestCase, override_settings

from certificates import crypto
from certificates.services import CertificateNotConfigured, get_cert_material, store_certificate
from compliance.tests.factories import fixture_cert_material
from submission.aeat_direct import (
    AeatDirectAdapter,
    SubmissionTransportError,
    outcome_from_response,
    parse_response,
)
from submission.gateway import SubmissionStatus

from .factories import (
    aceptado_con_errores_body,
    correcto_body,
    incorrecto_body,
    make_record,
)

ENDPOINT = "https://prewww1.aeat.test/VerifactuSOAP"
CERT_KEY = crypto.generate_key()


def _store_cert_for(owner):
    material, _ = fixture_cert_material()
    store_certificate(
        owner,
        p12_bytes=material.p12_bytes,
        passphrase=material.passphrase,
        subject=material.subject,
        not_after=material.not_after,
    )


class ResponseParsingTests(TestCase):
    def test_correcto_parses_to_accepted_with_csv(self):
        outcome = outcome_from_response(parse_response(correcto_body(csv="CSV-ABC")))
        self.assertIs(outcome.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(outcome.estado, "Correcto")
        self.assertEqual(outcome.csv, "CSV-ABC")

    def test_aceptado_con_errores_is_accepted_but_keeps_code(self):
        outcome = outcome_from_response(parse_response(aceptado_con_errores_body()))
        self.assertIs(outcome.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(outcome.aeat_code, "0002")

    def test_incorrecto_parses_to_rejected_with_code(self):
        outcome = outcome_from_response(parse_response(incorrecto_body(code="3000")))
        self.assertIs(outcome.status, SubmissionStatus.REJECTED)
        self.assertEqual(outcome.aeat_code, "3000")

    def test_verdictless_body_is_a_transport_fault(self):
        with self.assertRaises(SubmissionTransportError):
            outcome_from_response(parse_response("<ok/>"))


@override_settings(CERT_ENCRYPTION_KEY=CERT_KEY)
class AdapterSubmitTests(TestCase):
    def test_submit_uses_stored_cert_material_via_service(self):
        record = make_record()
        _store_cert_for(record.invoice.series.owner)
        captured = {}

        def fake_transport(url, soap_bytes, *, cert_material, timeout):
            captured["url"] = url
            captured["cert"] = cert_material
            captured["soap"] = soap_bytes
            return correcto_body(csv="CSV-OK")

        adapter = AeatDirectAdapter(endpoint=ENDPOINT, transport=fake_transport)
        outcome = adapter.submit(record)

        self.assertIs(outcome.status, SubmissionStatus.ACCEPTED)
        self.assertEqual(captured["url"], ENDPOINT)
        # The material is exactly what the sanctioned plaintext path returns.
        expected = get_cert_material(record.invoice.series.owner)
        self.assertEqual(captured["cert"].p12_bytes, expected.p12_bytes)
        # The submitted body is the full RegFactu envelope inside SOAP.
        self.assertIn(b"RegFactuSistemaFacturacion", captured["soap"])
        self.assertIn(b"Envelope", captured["soap"])

    def test_missing_certificate_propagates_and_skips_transport(self):
        record = make_record()  # owner has no stored certificate
        called = []
        adapter = AeatDirectAdapter(
            endpoint=ENDPOINT,
            transport=lambda *a, **k: called.append(1) or correcto_body(),
        )
        with self.assertRaises(CertificateNotConfigured):
            adapter.submit(record)
        self.assertEqual(called, [], "transport must not run without certificate material")

    def test_adapter_does_not_import_certificate_crypto(self):
        # Least-privilege: plaintext only via certificates.services, never crypto.
        import submission.aeat_direct as mod
        self.assertFalse(
            hasattr(mod, "decrypt"),
            "adapter must not pull certificates.crypto symbols into scope",
        )
