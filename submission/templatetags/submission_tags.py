from django import template

from submission.selectors import latest_alta_record, latest_submission_attempt

register = template.Library()


@register.simple_tag
def get_submission_badge(invoice):
    """Return submission status badge (color and text) for an invoice (T-032)."""
    record = latest_alta_record(invoice)

    if record is None:
        return {"color": "warning", "text": "Pendiente de registro Verifactu"}

    attempt = latest_submission_attempt(record)
    if attempt is None:
        return {"color": "secondary", "text": "Registro generado · sin enviar"}

    if attempt.status == "pending":
        return {"color": "info", "text": "Enviado · esperando respuesta AEAT"}
    elif attempt.status == "accepted":
        return {"color": "success", "text": "Aceptado por la AEAT ✓"}
    elif attempt.status == "rejected":
        return {"color": "danger", "text": "Rechazado por la AEAT"}

    return {"color": "secondary", "text": "Estado desconocido"}
