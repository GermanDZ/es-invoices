"""Tiny builders for client tests — no third-party factory lib needed."""
from django.contrib.auth import get_user_model

from clients.models import Client

_user_seq = 0


def make_user():
    global _user_seq
    _user_seq += 1
    return get_user_model().objects.create_user(
        username=f"autonomo{_user_seq}", password="x"
    )


def make_client(
    owner=None,
    fiscal_name="ACME SL",
    client_type=Client.ClientType.B2B,
    tax_id="A58818501",
    address="C/ Mayor 1",
):
    owner = owner or make_user()
    client = Client(
        owner=owner,
        fiscal_name=fiscal_name,
        client_type=client_type,
        tax_id=tax_id,
        address=address,
    )
    client.full_clean(exclude=["owner"], validate_unique=False)
    client.save()
    return client
