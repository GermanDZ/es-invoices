"""Issuance service (T-012 Operation 3) — the sole path that assigns a number.

``issue_invoice`` is where gap-free sequential numbering is guaranteed (R-02,
Q-1, AD-6). It runs inside a single transaction, takes a row lock on the series
(``select_for_update`` — a real lock on PostgreSQL, the production datastore;
a no-op on the SQLite test fallback), validates the invoice is issuable, assigns
``last_number + 1``, and advances the high-water mark — all atomically.

Two structural guarantees back it up so the invariant holds on either backend:

* ``(series, number)`` is unique (:class:`invoicing.models.Invoice`), so a
  duplicate can never be committed.
* A bounded retry catches the rare lost-update race the SQLite fallback can
  produce (no real row lock): the losing transaction rolls back and re-reads the
  advanced high-water mark, yielding the next number with **no gap and no
  duplicate**.

A validation failure raises out of the ``atomic`` block, so the transaction
rolls back and the series number is **not** consumed (UC-001 alt-flows 2a/6a,
requirement 5).
"""
from django.core.exceptions import ValidationError
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone

from .models import Invoice, Series

_MAX_RETRIES = 5


def _validate_issuable(invoice: Invoice) -> None:
    """Structural completeness an invoice needs to be issued at all.

    Deliberately *not* Verifactu legal-field validation — that is the versioned
    compliance module (AD-2 / T-013). Here: at least one line item plus the
    mandatory header fields.
    """
    if not invoice.items.exists():
        raise ValidationError("An invoice needs at least one line item to be issued.")
    missing = [
        name
        for name in ("recipient_name", "recipient_taxid")
        if not (getattr(invoice, name) or "").strip()
    ]
    if missing:
        raise ValidationError(f"Missing mandatory field(s): {', '.join(missing)}.")


def issue_invoice(invoice: Invoice) -> Invoice:
    """Validate, assign the next gap-free series number, persist. Returns it.

    Raises ``ValidationError`` (rolling back without consuming a number) when the
    invoice is not issuable.
    """
    if invoice.issued:
        raise ValidationError("Invoice is already issued.")

    last_error = None
    for _ in range(_MAX_RETRIES):
        try:
            with transaction.atomic():
                series = Series.objects.select_for_update().get(pk=invoice.series_id)
                _validate_issuable(invoice)

                invoice.number = series.last_number + 1
                invoice.issue_date = invoice.issue_date or timezone.now().date()
                invoice.issued = True
                totals = invoice.compute_totals()
                invoice.taxable_base = totals.taxable_base
                invoice.iva_total = totals.iva_total
                invoice.irpf_retention = totals.irpf_retention
                invoice.grand_total = totals.grand_total
                invoice.save()

                series.last_number = invoice.number
                series.save(update_fields=["last_number"])
            return invoice
        except (IntegrityError, OperationalError) as exc:
            # Lost-update / write-contention race on a lock-less backend: roll
            # back, reset the optimistic write state, and retry against the
            # now-advanced high-water mark.
            last_error = exc
            invoice.number = None
            invoice.issued = False
            continue

    raise last_error
