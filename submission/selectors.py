"""Read helpers over submission outcomes (T-023).

Pure queries shared by the submission UI (``submission.views``) and the invoice
detail page (``invoicing.views``): find the ``alta`` record a submission targets,
and tell whether it has already been accepted. Kept out of ``services.py`` (which
owns the write/retry/kill-switch policy and stays untouched) so the detail view can
import a query helper without depending on another app's view module.
"""
from __future__ import annotations

from compliance.models import VerifactuRecord

from .models import SubmissionAttempt


def latest_alta_record(invoice):
    """The most recent ``alta`` :class:`VerifactuRecord` for ``invoice``, or ``None``.

    An invoice may accrue an ``alta`` and a later ``anulacion``; submission from the
    UI targets the registration record, and ``-id`` picks the newest if more than
    one alta exists (rectificativa flows).
    """
    return (
        invoice.verifactu_records.filter(record_type=VerifactuRecord.ALTA)
        .order_by("-id")
        .first()
    )


def latest_submission_attempt(record):
    """The most recent :class:`SubmissionAttempt` for ``record``, or ``None``."""
    if record is None:
        return None
    return record.submission_attempts.order_by("-id").first()


def record_is_accepted(record) -> bool:
    """True when ``record`` already has an accepted submission attempt."""
    if record is None:
        return False
    return record.submission_attempts.filter(
        status=SubmissionAttempt.ACCEPTED
    ).exists()
