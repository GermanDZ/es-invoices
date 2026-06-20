"""Owner-scoped AEAT submission UI (T-023, UC-002).

The browser path for UC-002: from an issued invoice, submit its latest ``alta``
:class:`~compliance.models.VerifactuRecord` to the AEAT through
:func:`submission.services.submit_record` — the sole owner of the retry/pending
policy, the ``AEAT_SUBMISSION_LIVE`` kill-switch, and persisting the
:class:`~submission.models.SubmissionAttempt`. The view never makes a network call
or writes an attempt itself; it resolves ownership, guards, calls the engine, and
surfaces the outcome on the invoice detail page.

Owner-scoping mirrors the invoicing app: an :class:`Invoice` has no direct owner,
so the lookup filters ``series__owner=request.user`` — a cross-owner request is a
404, never a data leak (Requirement 6). An already-accepted record is not
re-submittable (Requirement 7).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from invoicing.models import Invoice

from .gateway import SubmissionStatus
from .selectors import latest_alta_record, record_is_accepted
from .services import submit_record


def _surface_outcome(request, outcome):
    """Translate a :class:`SubmissionOutcome` into a user-facing message."""
    status = outcome.status
    if status is SubmissionStatus.ACCEPTED:
        receipt = f" (CSV {outcome.csv})" if outcome.csv else ""
        messages.success(request, f"Registro aceptado por la AEAT{receipt}.")
    elif status is SubmissionStatus.REJECTED:
        detail = outcome.aeat_message or outcome.aeat_code or "sin detalle"
        messages.error(request, f"La AEAT rechazó el registro: {detail}. Corrige y reenvía.")
    elif status is SubmissionStatus.PENDING:
        reason = f" ({outcome.aeat_message})" if outcome.aeat_message else ""
        messages.warning(
            request,
            f"Envío pendiente: la AEAT no respondió{reason}. Habrá que reenviar.",
        )
    else:  # DISABLED — flag off, no attempt persisted
        messages.info(request, "El envío a la AEAT está deshabilitado en este entorno.")


@login_required
def submission_submit(request, invoice_pk):
    """Submit the invoice's latest ``alta`` record and surface the outcome.

    POST-only (GET redirects to the detail page). Refuses when there is no record
    yet or the record is already accepted — neither path makes a live call.
    """
    invoice = get_object_or_404(
        Invoice.objects.filter(series__owner=request.user), pk=invoice_pk
    )
    if request.method != "POST":
        return redirect("invoicing:detail", pk=invoice.pk)

    record = latest_alta_record(invoice)
    if record is None:
        messages.error(
            request, "La factura aún no tiene un registro Verifactu que enviar."
        )
        return redirect("invoicing:detail", pk=invoice.pk)
    if record_is_accepted(record):
        messages.info(
            request, "El registro ya fue aceptado por la AEAT; no se reenvía."
        )
        return redirect("invoicing:detail", pk=invoice.pk)

    outcome = submit_record(record)
    _surface_outcome(request, outcome)
    return redirect("invoicing:detail", pk=invoice.pk)
