"""Bridge a saved client into the invoice recipient snapshot (T-015 Operation 4).

The legal recipient record is the denormalised snapshot on
:class:`invoicing.models.Invoice` (T-012). ``recipient_snapshot`` produces those
fields from a saved :class:`clients.models.Client`, re-asserting the
type-conditional tax-id rule first — so a B2B client whose NIF is missing or
invalid cannot yield a usable snapshot for issuance (requirement 5).
"""
from .models import Client


def recipient_snapshot(client: Client) -> dict:
    """Return the invoice recipient fields for ``client``.

    Raises ``django.core.exceptions.ValidationError`` when the client cannot be
    used to issue an invoice (a B2B client with a missing/invalid NIF).
    """
    client.full_clean(exclude=["owner"], validate_unique=False)
    return {
        "recipient_name": client.fiscal_name,
        "recipient_taxid": client.tax_id,
        "recipient_address": client.address,
    }
