"""End-to-end tests for the six T-011 requirements (Operation 6).

Covers upload accept/reject (R1), encryption-at-rest inspection (R2), the
accessor configured/not-configured paths (R3), replace + account-deletion
cascade (R4), certificate-configured status (R5), and that the only decryption
path is the accessor (R6, with the static check in ``test_least_privilege``).
"""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from certificates import crypto, services
from certificates.models import UserCertificate
from certificates.services import CertificateNotConfigured

from .factories import make_p12

User = get_user_model()
KEY = crypto.generate_key()
PASSPHRASE = "s3cret"


def _upload_file(p12_bytes, name="cert.p12"):
    return SimpleUploadedFile(name, p12_bytes, content_type="application/x-pkcs12")


@override_settings(CERT_ENCRYPTION_KEY=KEY)
class UploadFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("autonomo", password="pw")
        self.client.force_login(self.user)
        self.url = reverse("certificates:upload")

    # R1 — accept a valid, unexpired P12 with the correct passphrase.
    def test_valid_upload_is_accepted_and_persisted(self):
        p12 = make_p12(PASSPHRASE.encode())
        resp = self.client.post(
            self.url,
            {"certificate_file": _upload_file(p12), "passphrase": PASSPHRASE},
        )
        self.assertRedirects(resp, self.url)
        self.assertTrue(UserCertificate.objects.filter(owner=self.user).exists())

    # R1 — wrong passphrase rejected, nothing persisted.
    def test_wrong_passphrase_rejected_and_nothing_persisted(self):
        p12 = make_p12(PASSPHRASE.encode())
        resp = self.client.post(
            self.url,
            {"certificate_file": _upload_file(p12), "passphrase": "wrong"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Could not load the certificate")
        self.assertFalse(UserCertificate.objects.filter(owner=self.user).exists())

    # R1 — a non-PKCS#12 file is rejected.
    def test_garbage_file_rejected(self):
        resp = self.client.post(
            self.url,
            {"certificate_file": _upload_file(b"not a p12 at all"), "passphrase": PASSPHRASE},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(UserCertificate.objects.filter(owner=self.user).exists())

    # R1 — an expired certificate is rejected.
    def test_expired_certificate_rejected(self):
        p12 = make_p12(PASSPHRASE.encode(), expired=True)
        resp = self.client.post(
            self.url,
            {"certificate_file": _upload_file(p12), "passphrase": PASSPHRASE},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "expired")
        self.assertFalse(UserCertificate.objects.filter(owner=self.user).exists())


@override_settings(CERT_ENCRYPTION_KEY=KEY)
class EncryptionAtRestTests(TestCase):
    def setUp(self):
        from django.utils import timezone

        self.user = User.objects.create_user("autonomo", password="pw")
        self.p12 = make_p12(PASSPHRASE.encode())
        services.store_certificate(
            self.user,
            p12_bytes=self.p12,
            passphrase=PASSPHRASE,
            subject="CN=Test Autonomo",
            not_after=timezone.now(),
        )

    # R2 — stored columns are ciphertext, not the original bytes/passphrase.
    def test_stored_material_is_ciphertext(self):
        rec = UserCertificate.objects.get(owner=self.user)
        self.assertNotIn(self.p12, bytes(rec.cert_ciphertext))
        self.assertNotEqual(bytes(rec.cert_ciphertext), self.p12)
        self.assertNotIn(PASSPHRASE.encode(), bytes(rec.passphrase_ciphertext))
        self.assertTrue(bytes(rec.cert_nonce))
        self.assertTrue(bytes(rec.passphrase_nonce))


@override_settings(CERT_ENCRYPTION_KEY=KEY)
class AccessorTests(TestCase):
    def setUp(self):
        from django.utils import timezone

        self.user = User.objects.create_user("autonomo", password="pw")
        self.other = User.objects.create_user("otro", password="pw")
        self.p12 = make_p12(PASSPHRASE.encode())
        services.store_certificate(
            self.user,
            p12_bytes=self.p12,
            passphrase=PASSPHRASE,
            subject="CN=Test Autonomo",
            not_after=timezone.now(),
        )

    # R3 — accessor returns usable decrypted material.
    def test_get_cert_material_round_trips(self):
        material = services.get_cert_material(self.user)
        self.assertEqual(material.p12_bytes, self.p12)
        self.assertEqual(material.passphrase, PASSPHRASE)

    # R3 — accessor raises (not returns empty) when nothing is configured.
    def test_get_cert_material_not_configured_raises(self):
        with self.assertRaises(CertificateNotConfigured):
            services.get_cert_material(self.other)

    # R5 — status reflects configuration.
    def test_status_configured_and_not(self):
        self.assertEqual(services.certificate_status(self.user), "configured")
        self.assertEqual(services.certificate_status(self.other), "not-configured")


@override_settings(CERT_ENCRYPTION_KEY=KEY)
class ReplaceAndDeleteTests(TestCase):
    def setUp(self):
        from django.utils import timezone

        self.now = timezone.now
        self.user = User.objects.create_user("autonomo", password="pw")

    def _store(self, p12):
        services.store_certificate(
            self.user,
            p12_bytes=p12,
            passphrase=PASSPHRASE,
            subject="CN=Test Autonomo",
            not_after=self.now(),
        )

    # R4 — re-upload overwrites; exactly one record, new material retrievable.
    def test_replace_overwrites_previous_material(self):
        first = make_p12(PASSPHRASE.encode(), common_name="First")
        second = make_p12(PASSPHRASE.encode(), common_name="Second")
        self._store(first)
        self._store(second)
        self.assertEqual(UserCertificate.objects.filter(owner=self.user).count(), 1)
        self.assertEqual(services.get_cert_material(self.user).p12_bytes, second)

    # R4 — deleting the owner cascades the certificate away.
    def test_account_deletion_cascades(self):
        self._store(make_p12(PASSPHRASE.encode()))
        self.user.delete()
        self.assertEqual(UserCertificate.objects.count(), 0)

    # R4 — explicit delete removes the stored material.
    def test_delete_certificate_removes_record(self):
        self._store(make_p12(PASSPHRASE.encode()))
        services.delete_certificate(self.user)
        self.assertFalse(UserCertificate.objects.filter(owner=self.user).exists())
