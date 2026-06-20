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


# Verifactu rectificativa subtypes (``TipoFactura`` R1–R5). Labelled in plain
# language so a zero-accounting-knowledge user can pick the reason without knowing
# the LIVA article numbers. The engine only varies the record's ``tipo_factura``;
# the method stays *por sustitución* (T-024 scope — *por diferencias* is T-025).
TIPO_RECTIFICATIVA_CHOICES = [
    ("R1", "R1 — Error en los datos o el importe (rectificación general)"),
    ("R2", "R2 — Concurso de acreedores del cliente"),
    ("R3", "R3 — Crédito incobrable"),
    ("R4", "R4 — Otros motivos"),
    ("R5", "R5 — Rectificación de factura simplificada"),
]


class RectificativaForm(forms.Form):
    """Issuer identity + correction reason for a *factura rectificativa* (UC-004).

    Mirrors :class:`IssuanceForm`'s issuer block (entered inline, carried in the
    session like T-022 DD1) and adds the ``tipo_factura`` reason selector. The
    corrected line items come from the separate :data:`LineItemFormSet`, pre-filled
    from the original via :func:`lineitem_initial_from`. It computes no totals and
    assigns no number — :func:`invoicing.services.issue_rectificativa` does.
    """

    issuer_name = forms.CharField(max_length=255, label="Nombre/Razón social del emisor")
    issuer_nif = forms.CharField(max_length=32, label="NIF del emisor")
    issuer_address = forms.CharField(
        max_length=255, required=False, label="Dirección del emisor"
    )
    issuer_email = forms.EmailField(required=False, label="Email del emisor")
    tipo_factura = forms.ChoiceField(
        choices=TIPO_RECTIFICATIVA_CHOICES,
        initial="R1",
        label="Motivo de la rectificación",
    )
    # Rectificativa method (T-025 R1). "S" sustitución restates the full corrected
    # invoice (default, today's behaviour); "I" por diferencias records only the
    # delta — the engine omits ImporteRectificacion for "I". The line-item form is
    # the same either way; the selector only switches TipoRectificativa.
    metodo = forms.ChoiceField(
        choices=[
            ("S", "Por sustitución (factura corregida completa)"),
            ("I", "Por diferencias (solo el importe rectificado)"),
        ],
        initial="S",
        label="Método de rectificación",
    )


def lineitem_initial_from(invoice):
    """Initial rows for the rectificativa :data:`LineItemFormSet` (UC-004 step 3).

    Pre-fills the corrected invoice *por sustitución* from the original's lines so
    the user edits the corrected figures rather than re-typing the whole invoice.
    """
    def _rate_choice(value):
        # Map the stored Decimal (e.g. 21.00) to the choice string ("21") by
        # numeric equality, so the pre-filled row selects the right option.
        return next(
            (str(r) for r in calc.IVA_RATES if r == value), str(value)
        )

    return [
        {
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "iva_rate": _rate_choice(item.iva_rate),
        }
        for item in invoice.items.all()
    ]
