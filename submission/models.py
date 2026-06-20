"""Persistence for AEAT submission outcomes (T-014).

A :class:`SubmissionAttempt` is the durable record of *one* submission of a
``compliance.VerifactuRecord`` to the AEAT — accepted (with the ``CSV`` receipt),
rejected (with the AEAT error code), or pending (transport never returned a verdict
after the bounded retries). The compliance record and the invoice are **never
mutated** by submission (both are append-only on identity); the outcome lives here,
keyed to the record, so a record may accrue more than one attempt (e.g. a pending
attempt later re-driven).
"""
from django.db import models


class SubmissionAttempt(models.Model):
    """One AEAT submission of a VerifactuRecord and its outcome."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"
    DISABLED = "disabled"
    # A pending attempt that was locally cancelled before AEAT returned a verdict
    # (T-025 R3 / UC-005 alt-flow 2a): annulling a still-pending invoice cancels
    # the in-flight submission instead of sending an anulación. Terminal — owned
    # by submission's vocabulary so callers never invent the string.
    CANCELLED = "cancelled"
    STATUSES = [
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (PENDING, "Pending"),
        (DISABLED, "Disabled"),
        (CANCELLED, "Cancelled"),
    ]

    record = models.ForeignKey(
        "compliance.VerifactuRecord",
        on_delete=models.PROTECT,
        related_name="submission_attempts",
    )
    status = models.CharField(max_length=10, choices=STATUSES)

    # AEAT response detail (RGPD: codes/CSV only — no NIF/name/cert material) ----
    estado = models.CharField(max_length=24, blank=True, default="")
    aeat_code = models.CharField(max_length=16, blank=True, default="")
    aeat_message = models.CharField(max_length=255, blank=True, default="")
    csv = models.CharField(max_length=64, blank=True, default="")

    retries = models.PositiveSmallIntegerField(default=0)
    aeat_env = models.CharField(max_length=16, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["record", "status"], name="idx_submission_record"),
        ]

    def __str__(self):
        return f"{self.status} {self.record_id} ({self.csv or self.aeat_code or '—'})"
