"""Owner-scoped CRUD + auth + B2B/B2C validation through the views (req. 1,2,3,4,6)."""
from django.test import TestCase
from django.urls import reverse

from clients.models import Client
from clients.tests.factories import make_client, make_user


class ClientViewTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        resp = self.client.get(reverse("clients:list"))
        self.assertEqual(resp.status_code, 302)

    def test_create_b2b_with_valid_taxid(self):
        resp = self.client.post(
            reverse("clients:create"),
            {
                "fiscal_name": "ACME SL",
                "client_type": "B2B",
                "tax_id": "A58818501",
                "address": "C/ Mayor 1",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Client.objects.filter(owner=self.user).count(), 1)

    def test_create_b2b_invalid_taxid_rejected(self):
        resp = self.client.post(
            reverse("clients:create"),
            {"fiscal_name": "ACME SL", "client_type": "B2B", "tax_id": "A58818500"},
        )
        self.assertEqual(resp.status_code, 200)  # re-render with field errors
        self.assertContains(resp, "valid Spanish tax")
        self.assertEqual(Client.objects.count(), 0)

    def test_create_b2b_missing_taxid_rejected(self):
        resp = self.client.post(
            reverse("clients:create"),
            {"fiscal_name": "ACME SL", "client_type": "B2B", "tax_id": ""},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Client.objects.count(), 0)

    def test_create_b2c_without_taxid_ok(self):
        resp = self.client.post(
            reverse("clients:create"),
            {"fiscal_name": "Juan Pérez", "client_type": "B2C", "tax_id": ""},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Client.objects.count(), 1)

    def test_create_b2c_invalid_taxid_rejected(self):
        resp = self.client.post(
            reverse("clients:create"),
            {"fiscal_name": "Juan", "client_type": "B2C", "tax_id": "BADID"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Client.objects.count(), 0)

    def test_cannot_open_another_users_client_edit(self):
        other = make_client(owner=make_user())
        resp = self.client.get(reverse("clients:edit", args=[other.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_cannot_delete_another_users_client(self):
        other = make_client(owner=make_user())
        resp = self.client.post(reverse("clients:delete", args=[other.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Client.objects.filter(pk=other.pk).exists())

    def test_edit_own_client(self):
        client = make_client(owner=self.user)
        resp = self.client.post(
            reverse("clients:edit", args=[client.pk]),
            {
                "fiscal_name": "ACME 2 SL",
                "client_type": "B2B",
                "tax_id": "A58818501",
                "address": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        client.refresh_from_db()
        self.assertEqual(client.fiscal_name, "ACME 2 SL")

    def test_list_shows_only_own_clients(self):
        make_client(owner=self.user, fiscal_name="Mine SL")
        make_client(owner=make_user(), fiscal_name="Theirs SL")
        resp = self.client.get(reverse("clients:list"))
        self.assertContains(resp, "Mine SL")
        self.assertNotContains(resp, "Theirs SL")
