"""recipient_snapshot bridges a client into the invoice snapshot (req. 5)."""
from django.core.exceptions import ValidationError
from django.test import TestCase

from clients.models import Client
from clients.services import recipient_snapshot
from clients.tests.factories import make_client


class RecipientSnapshotTests(TestCase):
    def test_snapshot_from_valid_b2b_client(self):
        client = make_client(
            fiscal_name="ACME SL", tax_id="A58818501", address="C/ Mayor 1"
        )
        self.assertEqual(
            recipient_snapshot(client),
            {
                "recipient_name": "ACME SL",
                "recipient_taxid": "A58818501",
                "recipient_address": "C/ Mayor 1",
            },
        )

    def test_snapshot_from_b2c_without_taxid(self):
        client = make_client(
            client_type=Client.ClientType.B2C, tax_id="", fiscal_name="Juan Pérez"
        )
        snap = recipient_snapshot(client)
        self.assertEqual(snap["recipient_name"], "Juan Pérez")
        self.assertEqual(snap["recipient_taxid"], "")

    def test_invalid_b2b_client_cannot_yield_snapshot(self):
        # Force a bad tax-id past the create-time guard, then snapshot at issue time.
        client = make_client()
        Client.objects.filter(pk=client.pk).update(
            tax_id="A58818500", client_type=Client.ClientType.B2B
        )
        client.refresh_from_db()
        with self.assertRaises(ValidationError):
            recipient_snapshot(client)
