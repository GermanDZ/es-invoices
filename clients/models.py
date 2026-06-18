"""Persistence for client/contact records (T-015 Operation 1).

A :class:`Client` is a reusable recipient owned by exactly one user
(architecture-notebook §4 "Client management"; scope.md S-1 / D-2). It carries
the fiscal data an invoice recipient needs — fiscal name, tax-id, address — and
a B2B/B2C type that governs whether the tax-id is mandatory:

* **B2B** — a business/professional: a Spanish NIF/CIF is **required** and
  checksum-validated.
* **B2C** — a final consumer (simplified-invoice rules, D-2): the tax-id is
  **optional**; when present it is still validated.

The legal recipient record on an issued invoice stays the denormalised snapshot
on :class:`invoicing.models.Invoice` (T-012); ``clients.services.recipient_snapshot``
bridges a saved client into those fields, and the nullable ``Invoice.client`` FK
records provenance only.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .validation import normalize_taxid, validate_spanish_taxid


class Client(models.Model):
    class ClientType(models.TextChoices):
        B2B = "B2B", "Business (NIF/CIF required)"
        B2C = "B2C", "Consumer (NIF/CIF optional)"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
    )
    fiscal_name = models.CharField(max_length=255)
    client_type = models.CharField(
        max_length=3, choices=ClientType.choices, default=ClientType.B2B
    )
    tax_id = models.CharField(max_length=32, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fiscal_name"]

    def __str__(self) -> str:
        return f"{self.fiscal_name} ({self.tax_id or 'sin NIF'})"

    def clean(self) -> None:
        """Normalise the tax-id and enforce the type-conditional rule.

        B2B requires a checksum-valid tax-id; B2C may omit it but validates a
        non-empty one. The error is attached to the ``tax_id`` field so both the
        model and any ``ModelForm`` surface it on the right input.
        """
        self.tax_id = normalize_taxid(self.tax_id)
        if self.client_type == self.ClientType.B2B and not self.tax_id:
            raise ValidationError({"tax_id": "A B2B client requires a NIF/CIF."})
        if self.tax_id:
            try:
                validate_spanish_taxid(self.tax_id)
            except ValidationError as exc:
                raise ValidationError({"tax_id": exc.messages})
