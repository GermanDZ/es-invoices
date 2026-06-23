"""Auth flow tests (T-021) — registration, login, logout, gating, landing.

The test runner already forces DEBUG=False, so ``config.urls`` registers the real
``accounts`` routes (the ``/dev/`` shim block is DEBUG-gated and absent here) — no
``ROOT_URLCONF`` override is needed, unlike the devtools shim tests.

Passwords used are length≥8, non-numeric, non-common, and dissimilar to the email
so they clear all four enabled validators; the weak/mismatch cases are exercised
explicitly.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

GOOD_PW = "barricade-7"


class RegistrationTests(TestCase):
    def test_register_creates_user_logs_in_and_redirects(self):
        # Requirement 1: unique email + matching valid passwords → user created
        # (username == lower-cased email), logged in, redirected to landing (→ invoicing:list).
        resp = self.client.post(
            reverse("accounts:register"),
            {"email": "Nuevo@Example.com", "password1": GOOD_PW, "password2": GOOD_PW},
        )
        # assertRedirects will see the redirect to landing; landing has target_status_code=302 (redirects again)
        self.assertRedirects(resp, reverse("accounts:landing"), target_status_code=302)
        user = User.objects.get(username="nuevo@example.com")
        self.assertEqual(user.email, "nuevo@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_duplicate_email_rejected(self):
        # Requirement 2: an existing email re-renders (200), creates no new user.
        User.objects.create_user(
            username="dup@example.com", email="dup@example.com", password=GOOD_PW
        )
        resp = self.client.post(
            reverse("accounts:register"),
            {"email": "dup@example.com", "password1": GOOD_PW, "password2": GOOD_PW},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(username="dup@example.com").count(), 1)

    def test_password_mismatch_rejected(self):
        # Requirement 2: differing passwords → 200, no user.
        resp = self.client.post(
            reverse("accounts:register"),
            {"email": "x@example.com", "password1": GOOD_PW, "password2": "different-9"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="x@example.com").exists())

    def test_weak_password_rejected(self):
        # Requirement 2: a validator failure (short + numeric + common) → 200, no user.
        resp = self.client.post(
            reverse("accounts:register"),
            {"email": "y@example.com", "password1": "12345", "password2": "12345"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username="y@example.com").exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user@example.com", email="user@example.com", password=GOOD_PW
        )

    def test_login_by_email_redirects_to_landing(self):
        # Requirement 3: correct email (any case) + password → 302 to landing (→ invoicing:list), session set.
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "User@Example.com", "password": GOOD_PW},
        )
        # assertRedirects will follow landing's redirect to invoicing:list
        self.assertRedirects(resp, reverse("accounts:landing"), target_status_code=302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_login_honors_safe_next(self):
        # Requirement 3: a safe ?next= overrides the default landing redirect.
        resp = self.client.post(
            reverse("accounts:login") + "?next=/clients/",
            {"username": "user@example.com", "password": GOOD_PW},
        )
        self.assertRedirects(resp, "/clients/")

    def test_wrong_password_no_session(self):
        # Requirement 3: bad password → 200, no session established.
        resp = self.client.post(
            reverse("accounts:login"),
            {"username": "user@example.com", "password": "wrong-pass-9"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_ends_session(self):
        # Requirement 4: POST logout clears the session and redirects.
        self.client.force_login(self.user)
        resp = self.client.post(reverse("accounts:logout"))
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class GatingAndLandingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com", email="owner@example.com", password=GOOD_PW
        )

    def test_anonymous_product_view_redirects_to_login(self):
        # Requirement 5: @login_required product view → 302 to LOGIN_URL?next=…
        resp = self.client.get(reverse("clients:list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])
        self.assertIn("next=", resp["Location"])

    def test_login_and_register_pages_public(self):
        # Requirement 5: auth entry points are not gated.
        self.assertEqual(self.client.get(reverse("accounts:login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:register")).status_code, 200)

    def test_anonymous_landing_redirects_to_login(self):
        # Requirement 5/6: the root landing is gated.
        resp = self.client.get(reverse("accounts:landing"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_landing_shows_user_and_links(self):
        # Requirement 6: landing redirects to invoicing:list, which shows user + nav links.
        self.client.force_login(self.user)
        resp = self.client.get(reverse("accounts:landing"), follow=True)
        self.assertEqual(resp.status_code, 200)
        # Check that we end up at invoicing:list
        self.assertEqual(resp.resolver_match.url_name, "list")
        # Check the navbar has the user email and links
        self.assertContains(resp, "owner@example.com")
        self.assertContains(resp, reverse("clients:list"))
        self.assertContains(resp, reverse("certificates:upload"))
