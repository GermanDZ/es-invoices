"""Builders for compliance tests — reuse the invoicing factories, then issue."""
from invoicing import services as invoicing_services
from invoicing.tests.factories import make_invoice, make_series, make_user

ISSUER_NIF = "B12345678"
ISSUER_NAME = "Autónomo de Prueba SL"


def issued_invoice(*, series=None, lines=None, irpf_rate="0",
                   recipient_name="Cliente SL", recipient_taxid="A82037292"):
    """Create and **issue** an invoice (number assigned, ``issued=True``)."""
    invoice = make_invoice(
        series=series,
        irpf_rate=irpf_rate,
        recipient_name=recipient_name,
        recipient_taxid=recipient_taxid,
        lines=lines or [(1, "100.00", "21")],
    )
    return invoicing_services.issue_invoice(invoice)
