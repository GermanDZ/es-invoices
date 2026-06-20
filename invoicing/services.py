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


def _original_alta(invoice):
    """The earliest alta VerifactuRecord for ``invoice`` (the one to act on)."""
    from compliance.models import VerifactuRecord

    return (
        invoice.verifactu_records.filter(record_type=VerifactuRecord.ALTA)
        .order_by("id")
        .first()
    )


def issue_rectificativa(rectificativa, original, *, issuer_nif, issuer_name,
                        tipo_factura="R1", method="S", fecha_hora=None,
                        signer=None, gateway=None):
    """Issue a draft ``rectificativa`` correcting ``original`` (UC-004).

    The caller builds the draft ``rectificativa`` like any invoice — its own
    (corrected, fully-restated) line items, recipient snapshot and a dedicated
    rectificativa ``series``. This verb then: issues it gap-free
    (:func:`issue_invoice`), generates a rectificativa-type *alta*
    (``TipoFactura=R1``) referencing ``original``'s alta record, submits it via
    the AD-3 gateway, and — on an **accepted or disabled** outcome — links
    ``original.corrected_by = rectificativa`` (a rejection leaves the original
    untouched; UC-004 9a). Returns ``(rectificativa, record, outcome)``.

    ``method`` selects the rectificativa type (UC-004 alt-flow 3a): ``"S"``
    *por sustitución* (default, today's behaviour — the record carries
    ``ImporteRectificacion``) or ``"I"`` *por diferencias* — the record carries
    ``TipoRectificativa="I"`` and emits no ``ImporteRectificacion``. The value
    flows straight to ``compliance.generate_alta`` which already supports both.
    """
    import compliance
    from submission.gateway import SubmissionStatus
    from submission.services import submit_record

    if not original.issued:
        raise ValidationError("Only an issued invoice can be corrected (UC-004).")
    original_record = _original_alta(original)
    if original_record is None:
        raise ValidationError("Original invoice has no alta record to rectify.")

    # Issue the rectificativa in its own series (gap-free; rolls back without
    # consuming a number if it is not issuable — requirement 6).
    issue_invoice(rectificativa)

    record = compliance.generate_alta(
        rectificativa,
        issuer_nif=issuer_nif,
        issuer_name=issuer_name,
        fecha_hora=fecha_hora,
        signer=signer,
        tipo_factura=tipo_factura,
        tipo_rectificativa=method,
        rectifies=original_record,
    )
    outcome = submit_record(record, gateway=gateway)
    if outcome.status in (SubmissionStatus.ACCEPTED, SubmissionStatus.DISABLED):
        original.corrected_by = rectificativa
        original.save(update_fields=["corrected_by"])
    return rectificativa, record, outcome


def annul_invoice(invoice, *, issuer_name=None, fecha_hora=None, signer=None,
                  gateway=None):
    """Annul an issued invoice's Verifactu record — sent-in-error only (UC-005).

    Reserved for records that should never have existed: **refuses** when the
    invoice already carries a rectificativa (``corrected_by`` set) — a real-sale
    correction belongs to :func:`issue_rectificativa` (UC-005 exception 2b).

    Two branches on the alta's submission state (UC-005):

    * **Pending** (alt-flow 2a) — the alta's latest :class:`SubmissionAttempt` is
      still ``pending`` at the AEAT: there is nothing registered to anul, so this
      **cancels the pending submission** (stamps that attempt ``cancelled``),
      marks the invoice ``annulled`` locally, generates **no** anulación record
      and sends nothing. Returns ``(None, None)``.
    * **Accepted / disabled** (the default) — reuses the shipped
      :func:`compliance.generate_anulacion` + the AD-3 gateway; on an accepted or
      disabled outcome marks ``invoice.annulled`` (a rejection leaves the prior
      state; UC-005 5a). Returns ``(record, outcome)``.

    Creates **no** new Invoice and consumes no series number in either branch.
    """
    import compliance
    from submission.gateway import SubmissionStatus
    from submission.models import SubmissionAttempt
    from submission.services import submit_record

    if not invoice.issued:
        raise ValidationError("Only an issued invoice can be annulled (UC-005).")
    if invoice.corrected_by_id is not None:
        raise ValidationError(
            "Invoice has a rectificativa; a real sale is corrected with a factura "
            "rectificativa, not annulled (UC-005)."
        )
    original_record = _original_alta(invoice)
    if original_record is None:
        raise ValidationError("Invoice has no alta record to annul.")

    # UC-005 alt-flow 2a: the alta is still pending at the AEAT — cancel the
    # in-flight submission instead of registering an anulación for a record that
    # was never accepted. Submission is synchronous today, so there is no external
    # queue to dequeue: stamping the latest pending attempt cancelled is the cancel.
    latest_attempt = original_record.submission_attempts.order_by("-id").first()
    if latest_attempt is not None and latest_attempt.status == SubmissionAttempt.PENDING:
        latest_attempt.status = SubmissionAttempt.CANCELLED
        latest_attempt.save(update_fields=["status"])
        invoice.annulled = True
        invoice.save(update_fields=["annulled"])
        return None, None

    record = compliance.generate_anulacion(
        original_record, issuer_name=issuer_name, fecha_hora=fecha_hora,
        signer=signer,
    )
    outcome = submit_record(record, gateway=gateway)
    if outcome.status in (SubmissionStatus.ACCEPTED, SubmissionStatus.DISABLED):
        invoice.annulled = True
        invoice.save(update_fields=["annulled"])
    return record, outcome
