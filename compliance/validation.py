"""Legal-field gate for Verifactu record generation (T-013 Operation 2).

A malformed record must never be generated or persisted (Q-1). This module is a
pure precondition check: given an issued invoice + the issuer identity, it raises
:class:`~django.core.exceptions.ValidationError` listing every missing mandatory
field, and the caller (:mod:`compliance.services`) only proceeds — and only then
persists — when this passes.
"""
from django.core.exceptions import ValidationError


def validate_issuable(invoice, *, issuer_nif, issuer_name):
    """Raise ``ValidationError`` if ``invoice`` cannot yield a Verifactu record.

    Checks the mandatory legal fields the AEAT record requires: the invoice must
    be issued (numbered), carry an issue date, name a recipient (fiscal id +
    name), have at least one line item, and the issuer identity must be supplied.
    """
    missing = []

    if not issuer_nif:
        missing.append("issuer_nif")
    if not issuer_name:
        missing.append("issuer_name")

    if not invoice.issued:
        missing.append("invoice.issued (only an issued invoice is reportable)")
    if invoice.number is None:
        missing.append("invoice.number")
    if invoice.issue_date is None:
        missing.append("invoice.issue_date")
    if not invoice.recipient_name:
        missing.append("recipient_name")
    if not invoice.recipient_taxid:
        missing.append("recipient_taxid")

    # At least one line item (PK required so .items works on a saved invoice).
    if invoice.pk is None or not invoice.items.exists():
        missing.append("line_items (at least one)")

    if missing:
        raise ValidationError(
            "Invoice is not Verifactu-issuable; missing/invalid: "
            + ", ".join(missing)
        )
