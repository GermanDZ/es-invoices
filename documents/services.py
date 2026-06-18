"""Document & delivery services (T-016, S-3 / UC-001 postcondition).

The architecture-notebook §4 "Document & delivery" module: render an
**already-issued** :class:`invoicing.models.Invoice` to a clean, legally complete
PDF and deliver it by email. This module is a *read-only consumer* of the
invoicing core — it never writes to an invoice, its line items, the numbering
series, or any compliance record (T-016 Requirement 5).

Issuer fiscal identity is **passed in** as an :class:`Issuer` value object, the
same boundary :func:`compliance.services.generate_alta` uses (``issuer_nif=`` /
``issuer_name=``) — this module adds no account/business model.

The Verifactu QR + "VERI*FACTU" legend on the PDF are sourced from the invoice's
**persisted** values formatted exactly as the Verifactu record was (NumSerie =
``prefix+number``, Fecha = ``DD-MM-YYYY``, Importe = ``taxable_base + iva_total``;
see :mod:`compliance.services` ``_num_serie`` / ``_fecha_exp`` and
:mod:`compliance.records` ``build_registro_alta``), so a scanned QR matches the
record AEAT received — never recomputed independently.
"""
import logging
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Success-measure instrumentation (T-016 §Success Measures): one INFO record per
# successful send, carrying NumSerie only — never the recipient address (RGPD).
# The delivery rate is `invoice_email_sent` count / issued-invoice count.
logger = logging.getLogger("documents")


@dataclass(frozen=True)
class Issuer:
    """The issuing business's fiscal identity — caller-supplied, not persisted."""

    name: str
    nif: str
    address: str = ""
    email: str = ""


def _require_issued(invoice) -> None:
    """Guard: only an issued invoice has the numbered, immutable legal record a
    PDF/email may expose (T-016 Requirement 4)."""
    if not getattr(invoice, "issued", False) or invoice.number is None:
        raise ValidationError("Cannot render/send a not-yet-issued invoice.")


def _num_serie(invoice) -> str:
    """NumSerieFactura — series prefix + assigned number. Mirrors
    ``compliance.services._num_serie`` (the value AEAT received)."""
    return f"{invoice.series.prefix}{invoice.number}"


def _fecha_exp(invoice) -> str:
    """FechaExpedicionFactura in AEAT DD-MM-YYYY form. Mirrors
    ``compliance.services._fecha_exp``."""
    return invoice.issue_date.strftime("%d-%m-%Y")


def _importe_total(invoice) -> str:
    """Verifactu ImporteTotal = taxable_base + iva_total (IRPF is NOT subtracted),
    2 decimals — mirrors ``compliance.records.build_registro_alta``."""
    total = Decimal(invoice.taxable_base) + Decimal(invoice.iva_total)
    return f"{total:.2f}"


def build_qr_url(invoice, issuer) -> str:
    """The AEAT VERI*FACTU public-verification URL the PDF QR encodes.

    ``VERIFACTU_QR_BASE_URL`` (preproducción by default) plus the issuer NIF and
    the invoice's persisted NumSerie / Fecha / Importe as query parameters.
    """
    params = urlencode(
        {
            "nif": issuer.nif,
            "numserie": _num_serie(invoice),
            "fecha": _fecha_exp(invoice),
            "importe": _importe_total(invoice),
        }
    )
    return f"{settings.VERIFACTU_QR_BASE_URL}?{params}"


def _qr_data_uri(url: str) -> str:
    """A scannable QR for ``url`` as a self-contained PNG ``data:`` URI.

    ``segno`` writes PNG natively (no Pillow / native deps), and WeasyPrint
    embeds the data URI directly — so the PDF carries the QR with no external
    asset or filesystem write.
    """
    import io

    import segno

    buf = io.BytesIO()
    segno.make(url, error="m").save(buf, kind="png", scale=4, border=2)
    import base64

    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def render_invoice_pdf(invoice, *, issuer) -> bytes:
    """Render an issued ``invoice`` to PDF bytes (T-016 Requirements 1, 2, 5).

    Read-only: totals/groups are recomputed from the persisted line items for the
    IVA breakdown, but nothing is written back. The returned bytes carry every
    mandatory legal field plus the VERI*FACTU legend and verification QR.
    """
    from weasyprint import HTML

    from invoicing import calc

    _require_issued(invoice)
    totals = invoice.compute_totals()
    qr_url = build_qr_url(invoice, issuer)
    lines = [
        {
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "iva_rate": item.iva_rate,
            "amount": calc.line_amount(item.quantity, item.unit_price),
        }
        for item in invoice.items.all()
    ]
    html = render_to_string(
        "documents/invoice.html",
        {
            "invoice": invoice,
            "issuer": issuer,
            "items": lines,
            "totals": totals,
            "num_serie": _num_serie(invoice),
            "fecha_exp": _fecha_exp(invoice),
            "qr_data_uri": _qr_data_uri(qr_url),
        },
    )
    return HTML(string=html).write_pdf()


def send_invoice_email(invoice, *, issuer, to_email=None, body=None):
    """Render ``invoice`` and email the PDF as an attachment (T-016 Requirement 3).

    Uses Django's configured email backend (console in dev, SMTP in production —
    config, not code). ``to_email`` defaults to the recipient's saved client
    email when not given; a missing address raises rather than silently dropping.
    Returns the number of messages sent (Django's ``EmailMessage.send`` contract).
    """
    _require_issued(invoice)
    recipient = to_email or _recipient_email(invoice)
    if not recipient:
        raise ValidationError(
            "No recipient email: pass to_email or set the client's email."
        )

    num_serie = _num_serie(invoice)
    pdf = render_invoice_pdf(invoice, issuer=issuer)
    subject = f"Factura {num_serie} — {issuer.name}"
    text = body or (
        f"Estimado/a {invoice.recipient_name}:\n\n"
        f"Adjuntamos la factura {num_serie} con fecha {_fecha_exp(invoice)} "
        f"por un importe total de {invoice.grand_total} €.\n\n"
        f"Un saludo,\n{issuer.name}"
    )
    message = EmailMessage(
        subject=subject,
        body=text,
        from_email=issuer.email or settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    message.attach(f"factura-{num_serie}.pdf", pdf, "application/pdf")
    sent = message.send()
    if sent:
        # Instrumentation only — NumSerie, no recipient PII (RGPD).
        logger.info("invoice_email_sent num_serie=%s", num_serie)
    return sent


def _recipient_email(invoice) -> str:
    """Best-effort recipient address from the invoice.

    Neither the recipient snapshot (T-012) nor the ``clients.Client`` model
    (T-015) carries an email field today, so this currently yields '' and
    ``to_email`` must be supplied by the caller. The ``getattr`` is
    forward-compatible: if a ``Client.email`` field is added later, an invoice
    carrying the provenance FK will resolve it automatically — no change here."""
    client = getattr(invoice, "client", None)
    return getattr(client, "email", "") or ""
