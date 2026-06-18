"""Submission orchestration (T-014 Operation 4).

``submit_record`` is the verb the rest of the app calls. It owns the policy the
adapter deliberately does not: the ``AEAT_SUBMISSION_ENABLED`` kill-switch, the
bounded transport-retry → ``pending`` degradation, and persisting the
:class:`~submission.models.SubmissionAttempt`. The adapter (AD-3) stays a pure
transport; swapping a gateway adapter in changes nothing here.
"""
from __future__ import annotations

from django.conf import settings

from .aeat_direct import AeatDirectAdapter, SubmissionTransportError
from .gateway import SubmissionGateway, SubmissionOutcome, SubmissionStatus
from .models import SubmissionAttempt


def _default_gateway() -> SubmissionGateway:
    """Build the configured direct adapter from settings (preproducción default)."""
    return AeatDirectAdapter(
        endpoint=settings.AEAT_ENDPOINT,
        timeout=getattr(settings, "AEAT_SUBMISSION_TIMEOUT", 45),
    )


def _persist(record, outcome: SubmissionOutcome) -> SubmissionAttempt:
    return SubmissionAttempt.objects.create(
        record=record,
        status=outcome.status.value,
        estado=outcome.estado or "",
        aeat_code=outcome.aeat_code or "",
        aeat_message=(outcome.aeat_message or "")[:255],
        csv=outcome.csv or "",
        retries=outcome.retries,
        aeat_env=getattr(settings, "AEAT_ENV", ""),
    )


def submit_record(record, *, gateway: SubmissionGateway | None = None) -> SubmissionOutcome:
    """Submit ``record`` to the AEAT and persist the outcome.

    Returns the :class:`SubmissionOutcome`. When ``AEAT_SUBMISSION_ENABLED`` is
    falsey the call short-circuits **before** any cert resolution or network call
    and persists no attempt (a ``DISABLED`` outcome). Transport failures retry up to
    ``AEAT_SUBMISSION_MAX_RETRIES`` times then persist a ``pending`` attempt; a
    business ``Incorrecto`` rejection is never retried.
    """
    if not getattr(settings, "AEAT_SUBMISSION_ENABLED", False):
        return SubmissionOutcome(status=SubmissionStatus.DISABLED)

    gateway = gateway or _default_gateway()
    max_retries = getattr(settings, "AEAT_SUBMISSION_MAX_RETRIES", 3)

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):  # 1 initial try + N retries
        try:
            outcome = gateway.submit(record)
        except SubmissionTransportError as exc:
            last_error = exc
            continue  # transport fault — retry
        # A verdict (accepted/rejected) is terminal — no retry, even on rejection.
        outcome = SubmissionOutcome(
            status=outcome.status,
            estado=outcome.estado,
            aeat_code=outcome.aeat_code,
            aeat_message=outcome.aeat_message,
            csv=outcome.csv,
            retries=attempt,
            raw=outcome.raw,
        )
        _persist(record, outcome)
        return outcome

    # Exhausted every attempt on transport faults — degrade to pending (never lost).
    outcome = SubmissionOutcome(
        status=SubmissionStatus.PENDING,
        aeat_message=str(last_error)[:255] if last_error else "",
        retries=max_retries,
    )
    _persist(record, outcome)
    return outcome
