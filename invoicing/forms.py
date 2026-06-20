"""Issuance UI forms (T-022 Operation 1).

The browser surface over the issuance engine. None of these forms compute totals,
assign numbers, or validate legal fields — that stays in
:mod:`invoicing.services` / :mod:`invoicing.calc`. They only collect input:

* :class:`IssuanceForm` — the issuer fiscal identity (entered inline, carried in
  the session, never persisted — see ``docs/changes/T-022/design.md`` DD1), the
  recipient (a saved owner-scoped :class:`clients.models.Client`, DD2), and the
  invoice-level IRPF rate.
* :class:`LineItemForm` / :data:`LineItemFormSet` — one row each
  (description, quantity, unit price, IVA rate); ``issue_invoice`` is the
  authority on "at least one line item", so the formset itself sets no minimum.
"""
from decimal import Decimal

from django import forms

from clients.models import Client
from invoicing import calc

# Legal IVA rates, as (value, label) choices, so the UI cannot offer a rate the
# arithmetic module would treat as exempt-by-accident.
IVA_RATE_CHOICES = [(str(r), f"{r}%") for r in calc.IVA_RATES]


class IssuanceForm(forms.Form):
    """Issuer identity + recipient client + IRPF rate for a new invoice."""

    issuer_name = forms.CharField(max_length=255, label="Nombre/Razón social del emisor")
    issuer_nif = forms.CharField(max_length=32, label="NIF del emisor")
    issuer_address = forms.CharField(
        max_length=255, required=False, label="Dirección del emisor"
    )
    issuer_email = forms.EmailField(required=False, label="Email del emisor")

    client = forms.ModelChoiceField(
        queryset=Client.objects.none(), label="Cliente (destinatario)"
    )
    irpf_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("100"),
        initial=Decimal("0"),
        label="Retención IRPF (%)",
    )

    def __init__(self, *args, owner=None, **kwargs):
        """``owner`` scopes the client choices to the logged-in user (DD2)."""
        super().__init__(*args, **kwargs)
        if owner is not None:
            self.fields["client"].queryset = Client.objects.filter(owner=owner)


class LineItemForm(forms.Form):
    """One invoice line. Empty rows (no description) are skipped by the view."""

    description = forms.CharField(max_length=255, required=False)
    quantity = forms.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal("0"), required=False
    )
    unit_price = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False
    )
    iva_rate = forms.ChoiceField(choices=IVA_RATE_CHOICES, required=False)

    def is_filled(self):
        """A row counts only when it carries a description (the view's filter)."""
        return bool((self.cleaned_data.get("description") or "").strip())

    def clean(self):
        """A filled row must carry quantity and unit price; empty rows pass."""
        cleaned = super().clean()
        if (cleaned.get("description") or "").strip():
            if cleaned.get("quantity") is None:
                self.add_error("quantity", "Indica la cantidad.")
            if cleaned.get("unit_price") is None:
                self.add_error("unit_price", "Indica el precio unitario.")
        return cleaned


LineItemFormSet = forms.formset_factory(LineItemForm, extra=3)
