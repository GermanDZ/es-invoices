"""Tiny builders for invoicing tests — no third-party factory lib needed."""
from decimal import Decimal

from django.contrib.auth import get_user_model

from invoicing.models import Invoice, LineItem, Series

_user_seq = 0


def make_user():
    global _user_seq
    _user_seq += 1
    return get_user_model().objects.create_user(
        username=f"autonomo{_user_seq}", password="x"
    )


def make_series(owner=None, prefix=""):
    return Series.objects.create(owner=owner or make_user(), prefix=prefix)


def make_invoice(series=None, irpf_rate="0", recipient_name="Cliente SL",
                 recipient_taxid="B12345678", lines=None):
    """Create a draft invoice with optional line items.

    ``lines`` is a list of ``(quantity, unit_price, iva_rate)`` tuples.
    """
    series = series or make_series()
    invoice = Invoice.objects.create(
        series=series,
        irpf_rate=Decimal(irpf_rate),
        recipient_name=recipient_name,
        recipient_taxid=recipient_taxid,
    )
    for quantity, unit_price, iva_rate in (lines or []):
        LineItem.objects.create(
            invoice=invoice,
            description="x",
            quantity=Decimal(str(quantity)),
            unit_price=Decimal(str(unit_price)),
            iva_rate=Decimal(str(iva_rate)),
        )
    return invoice
