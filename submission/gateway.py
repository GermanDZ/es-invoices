"""The AD-3 submission boundary (T-014 Operation 2).

Callers depend only on :class:`SubmissionGateway` and the :class:`SubmissionOutcome`
it returns — never on an adapter's concrete type. The v1 implementation is the
direct AEAT adapter (:mod:`submission.aeat_direct`); R-03's pre-agreed fallback is a
gateway-provider adapter satisfying this same interface, swappable without touching
``submission.services`` (AD-3).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum


class SubmissionStatus(str, Enum):
    """The verdict of a submission attempt.

    ``ACCEPTED`` folds the AEAT ``Correcto`` and ``AceptadoConErrores`` estados (the
    record is registered; the latter carries a non-fatal code). ``REJECTED`` is a
    business ``Incorrecto`` — the record is invalid and must be corrected, never
    blindly resubmitted. ``PENDING`` means the transport never yielded a verdict
    after the bounded retries (queued for a later re-drive). ``DISABLED`` is the
    flag-off short-circuit — no call was made.
    """

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"
    DISABLED = "disabled"


@dataclass(frozen=True)
class SubmissionOutcome:
    """The structured result of one submission, independent of the adapter.

    ``estado`` is the raw AEAT estado string (``Correcto`` / ``AceptadoConErrores`` /
    ``Incorrecto``) when one was returned; ``aeat_code`` / ``aeat_message`` carry the
    per-record error detail; ``csv`` is the acceptance receipt. ``retries`` is how
    many transport retries were spent reaching this outcome.
    """

    status: SubmissionStatus
    estado: str | None = None
    aeat_code: str | None = None
    aeat_message: str | None = None
    csv: str | None = None
    retries: int = 0
    raw: dict = field(default_factory=dict)

    @property
    def is_accepted(self) -> bool:
        return self.status is SubmissionStatus.ACCEPTED


class SubmissionGateway(abc.ABC):
    """One operation: submit a record, get a verdict. The AD-3 seam."""

    @abc.abstractmethod
    def submit(self, record) -> SubmissionOutcome:
        """Submit a ``compliance.VerifactuRecord`` and return its outcome.

        Implementations may raise on a *transport* failure (the orchestration in
        :mod:`submission.services` owns the retry/pending policy); a *business*
        rejection must come back as a :class:`SubmissionOutcome` with
        ``status=REJECTED``, not an exception.
        """
        raise NotImplementedError
