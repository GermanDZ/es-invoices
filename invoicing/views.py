"""Owner-scoped invoice issuance UI (T-022 Operations 2–3).

The browser path for UC-001: build a draft invoice with line items, issue it
through :func:`invoicing.services.issue_invoice` (the sole numbering authority —
the views never assign a number or compute a total), then retrieve the rendered
PDF and send it by email via :mod:`documents.services`.

Owner-scoping mirrors the clients/certificates apps: an :class:`Invoice` has no
direct owner, so every lookup filters by ``series__owner=request.user`` — a
cross-owner request is a 404, never a data leak (Requirement 8). The issuer
fiscal identity is carried in the session (DD1), not persisted.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from clients.services import recipient_snapshot
from documents.services import Issuer, render_invoice_pdf, send_invoice_email
from submission.selectors import latest_alta_record, record_is_accepted

from .forms import IssuanceForm, LineItemFormSet
from .models import Invoice, LineItem, Series

_SESSION_ISSUER_KEY = "issuer"


def _owner_invoices(user):
    """Invoices visible to ``user`` — scoped through the series owner."""
    return Invoice.objects.filter(series__owner=user)


def _issuer_from_session(request):
    """Rebuild the :class:`Issuer` value object from the session, or ``None``."""
    data = request.session.get(_SESSION_ISSUER_KEY)
    if not data:
        return None
    return Issuer(
        name=data.get("name", ""),
        nif=data.get("nif", ""),
        address=data.get("address", ""),
        email=data.get("email", ""),
    )


@login_required
def invoice_create(request):
    """Build a draft, issue it in one atomic step (DD3), redirect to detail.

    A ``ValidationError`` from the engine (no line items → alt-2a; missing
    recipient field → alt-6a) rolls the draft back and re-renders the form with
    the message; ``issue_invoice`` guarantees the series number is not consumed.
    """
    if request.method == "POST":
        form = IssuanceForm(request.POST, owner=request.user)
        formset = LineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                invoice = _issue_from_forms(request.user, form, formset)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
            else:
                # Carry the issuer for the post-issuance PDF/send requests (DD1).
                request.session[_SESSION_ISSUER_KEY] = {
                    "name": form.cleaned_data["issuer_name"],
                    "nif": form.cleaned_data["issuer_nif"],
                    "address": form.cleaned_data["issuer_address"],
                    "email": form.cleaned_data["issuer_email"],
                }
                messages.success(request, f"Factura {invoice} emitida.")
                return redirect("invoicing:detail", pk=invoice.pk)
    else:
        form = IssuanceForm(
            owner=request.user, initial=_issuer_initial(request)
        )
        formset = LineItemFormSet()
    return render(
        request,
        "invoicing/invoice_form.html",
        {"form": form, "formset": formset},
    )


def _issuer_initial(request):
    """Prefill the create form's issuer fields from the last session issuer."""
    data = request.session.get(_SESSION_ISSUER_KEY) or {}
    return {
        "issuer_name": data.get("name", ""),
        "issuer_nif": data.get("nif", ""),
        "issuer_address": data.get("address", ""),
        "issuer_email": data.get("email", ""),
    }


def _issue_from_forms(user, form, formset):
    """Create the draft + line items and issue, all within one transaction.

    Raises ``ValidationError`` (rolling everything back) when the draft is not
    issuable. Returns the issued invoice.
    """
    series, _ = Series.objects.get_or_create(owner=user, prefix="")
    client = form.cleaned_data["client"]
    with transaction.atomic():
        invoice = Invoice.objects.create(
            series=series,
            client=client,
            irpf_rate=form.cleaned_data["irpf_rate"],
            **recipient_snapshot(client),
        )
        for row in formset:
            if row.is_filled():
                LineItem.objects.create(
                    invoice=invoice,
                    description=row.cleaned_data["description"],
                    quantity=row.cleaned_data["quantity"],
                    unit_price=row.cleaned_data["unit_price"],
                    iva_rate=row.cleaned_data["iva_rate"],
                )
        from .services import issue_invoice

        return issue_invoice(invoice)


@login_required
def invoice_detail(request, pk):
    """Show an issued (or draft) invoice with PDF, send, and AEAT-submit actions.

    The AEAT submission panel (T-023) surfaces the latest ``alta`` record's
    attempts and whether a submit is still available; the submit itself POSTs to
    ``submission:submit`` (the engine owns the call).
    """
    invoice = get_object_or_404(_owner_invoices(request.user), pk=pk)
    record = latest_alta_record(invoice)
    attempts = list(record.submission_attempts.order_by("-id")) if record else []
    return render(
        request,
        "invoicing/invoice_detail.html",
        {
            "invoice": invoice,
            "totals": invoice.compute_totals(),
            "submission_record": record,
            "submission_attempts": attempts,
            "submission_can_submit": record is not None and not record_is_accepted(record),
        },
    )


@login_required
def invoice_pdf(request, pk):
    """Stream the rendered PDF (Requirement 5). Issuer from the session (DD1)."""
    invoice = get_object_or_404(_owner_invoices(request.user), pk=pk)
    issuer = _issuer_from_session(request)
    if issuer is None:
        messages.error(request, "Vuelve a introducir los datos del emisor.")
        return redirect("invoicing:detail", pk=pk)
    try:
        pdf = render_invoice_pdf(invoice, issuer=issuer)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("invoicing:detail", pk=pk)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="factura-{invoice.series.prefix}{invoice.number}.pdf"'
    )
    return response


@login_required
def invoice_send(request, pk):
    """Email the invoice PDF to an address from the form (Requirement 6)."""
    invoice = get_object_or_404(_owner_invoices(request.user), pk=pk)
    if request.method != "POST":
        return redirect("invoicing:detail", pk=pk)
    issuer = _issuer_from_session(request)
    if issuer is None:
        messages.error(request, "Vuelve a introducir los datos del emisor.")
        return redirect("invoicing:detail", pk=pk)
    to_email = (request.POST.get("to_email") or "").strip()
    try:
        sent = send_invoice_email(invoice, issuer=issuer, to_email=to_email or None)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        if sent:
            messages.success(request, f"Factura enviada a {to_email}.")
        else:
            messages.error(request, "No se pudo enviar el email.")
    return redirect("invoicing:detail", pk=pk)
