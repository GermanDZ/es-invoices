"""Client create/edit form (T-015 Operation 3).

A thin ``ModelForm`` over :class:`clients.models.Client`. The type-conditional
tax-id rule lives in ``Client.clean`` and runs automatically via the model's
``full_clean`` during ``ModelForm`` validation, so the form stays declarative and
the rule has a single home (no duplication between form and model).
"""
from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["fiscal_name", "client_type", "tax_id", "address"]
