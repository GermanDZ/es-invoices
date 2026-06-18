"""Persistence for the invoicing core (T-012 Operation 1).

Three entities under the architecture-notebook §4 "Invoicing core":

* :class:`Series` — a per-business numbering series carrying the gap-free
  high-water mark (``last_number``). Issuance advances it under a row lock
  (:func:`invoicing.services.issue_invoice`).
* :class:`Invoice` — the header: the assigned number, the **recipient fiscal
  snapshot** (denormalised — client CRUD is T-015), the invoice-level IRPF rate,
  and the computed totals persisted at issue time so downstream modules (T-013
  record generation, T-016 PDF) read a stable, already-numbered record.
* :class:`LineItem` — description, quantity, unit price and per-line IVA rate.

Gap-free numbering is enforced structurally: ``(series, number)`` is unique, and
an issued invoice is immutable on its identifying fields (number, issue date,
series) — see :meth:`Invoice.save`.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from . import calc


class Series(models.Model):
    """A numbering series for one issuing business (scope.md D-3: ≥1 per user)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoice_series",
    )
    prefix = models.CharField(max_length=16, blank=True, default="")
    # Gap-free high-water mark; the number of the most recently issued invoice.
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "prefix"], name="uniq_series_owner_prefix"
            )
        ]

    def __str__(self):
        return f"{self.prefix or '(default)'} @ {self.last_number}"


class Invoice(models.Model):
    """An invoice header. Draft until issued; immutable on identity once issued."""

    # Identifying / numbering -------------------------------------------------
    series = models.ForeignKey(
        Series, on_delete=models.PROTECT, related_name="invoices"
    )
    number = models.PositiveIntegerField(null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    issued = models.BooleanField(default=False)

    # Recipient fiscal snapshot (denormalised) — the legal record. The optional
    # client FK below records provenance only (T-015); the snapshot remains the
    # source of truth and is never displaced by it.
    recipient_name = models.CharField(max_length=255)
    recipient_taxid = models.CharField(max_length=32)
    recipient_address = models.CharField(max_length=255, blank=True, default="")

    # Provenance: which saved client (if any) this invoice's recipient came from.
    # Nullable + additive; never read by numbering or the compliance module.
    client = models.ForeignKey(
        "clients.Client",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    # Corrective / cancellation linkage (T-017, S-5) --------------------------
    # ``corrected_by`` points an issued original at the factura rectificativa that
    # supersedes it (UC-004); the reverse manager ``corrects`` gives the
    # rectificativa its reference back to the original(s) it corrects. ``annulled``
    # marks a record voided in error (UC-005) — excluded from the active set but
    # never deleted. Both are set *after* issuance and are therefore deliberately
    # absent from ``_IMMUTABLE_WHEN_ISSUED`` (post-issue mutation is allowed).
    corrected_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="corrects",
    )
    annulled = models.BooleanField(default=False)

    # Tax config + persisted computed totals (filled at issue time) -----------
    irpf_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0")
    )
    taxable_base = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    iva_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    irpf_retention = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )
    grand_total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0")
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["series", "number"], name="uniq_invoice_series_number"
            )
        ]

    # Fields that must never change once the invoice is issued (legal identity).
    _IMMUTABLE_WHEN_ISSUED = ("series_id", "number", "issue_date")

    def __str__(self):
        return f"{self.series.prefix}{self.number or '—'}"

    def compute_totals(self):
        """Recompute totals from the current line items (does not save)."""
        return calc.compute_totals(self.items.all(), irpf_rate=self.irpf_rate)

    def save(self, *args, **kwargs):
        """Reject mutation of identifying fields on an already-issued invoice.

        Requirement 6: an issued invoice is append-only on its numbering/identity
        fields so downstream modules read a stable record.
        """
        if self.pk:
            prior = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(*self._IMMUTABLE_WHEN_ISSUED, "issued")
                .first()
            )
            if prior and prior["issued"]:
                for fieldname in self._IMMUTABLE_WHEN_ISSUED:
                    if getattr(self, fieldname) != prior[fieldname]:
                        raise ValidationError(
                            f"{fieldname} is immutable on an issued invoice."
                        )
        super().save(*args, **kwargs)


class LineItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items"
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    iva_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.description
