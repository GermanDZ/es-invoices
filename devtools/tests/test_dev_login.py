"""Tests for the dev-only auth shim (T-020).

Django's test runner forces ``settings.DEBUG = False`` at urlconf-load time, so
``config.urls`` never registers the DEBUG-gated ``/dev/`` routes under
``manage.py test``. These tests therefore swap in ``devtools.tests.urls`` (which
wires the routes unconditionally) via ``override_settings(ROOT_URLCONF=...)`` to
assert the wiring, and drive the view's own ``settings.DEBUG`` guard separately —
the testable production-safety enforcement point (an INSTALLED_APPS / cold-urlconf
assertion would need a fresh process; see plan Self-Critique §3).
"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(DEBUG=True, ROOT_URLCONF="devtools.tests.urls")
class DevLoginViewTests(TestCase):
    def test_authenticates_and_redirects_to_configured_landing(self):
        resp = self.client.get(reverse("devtools:login"))
        # assertRedirects follows to /clients/ and asserts the final 200 — which
        # only holds because the session is now authenticated (end-to-end unblock).
        self.assertRedirects(resp, "/clients/")
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="dev").pk,
        )

    def test_product_pages_reachable_after_dev_login(self):
        self.client.get(reverse("devtools:login"))
        self.assertEqual(self.client.get("/clients/").status_code, 200)
        self.assertEqual(self.client.get("/certificate/").status_code, 200)

    def test_root_redirects_to_dev_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/dev/login/")

    @override_settings(DEBUG=False)
    def test_dev_login_404s_when_debug_off(self):
        # Route still resolves (test urlconf), so the view's guard is what refuses
        # — and no session is created.
        resp = self.client.get(reverse("devtools:login"))
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn("_auth_user_id", self.client.session)

    @override_settings(DEV_LOGIN_REDIRECT="/certificate/")
    def test_landing_is_overridable(self):
        resp = self.client.get(reverse("devtools:login"))
        self.assertEqual(resp["Location"], "/certificate/")


class SeedDevOwnerCommandTests(TestCase):
    def test_seed_is_idempotent_and_user_can_authenticate(self):
        call_command("seed_dev_owner")
        call_command("seed_dev_owner")
        self.assertEqual(User.objects.filter(username="dev").count(), 1)
        # Password was set, so the standard ModelBackend authenticates it.
        self.assertTrue(self.client.login(username="dev", password="dev"))
