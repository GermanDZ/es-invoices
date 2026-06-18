"""Transactional orchestration for the compliance module (T-013 Ops 5 & 6).

``generate_alta`` / ``generate_anulacion`` are the verbs the rest of the app
calls. Each opens one :func:`transaction.atomic` block, **row-locks the issuer's
chain head** (:class:`~compliance.models.IssuerChain`) so concurrent generation
cannot fork the hash chain (mirrors T-012's ``select_for_update`` numbering,
AD-6/Q-1), computes the chained ``huella``, optionally signs, and persists one
:class:`~compliance.models.VerifactuRecord` advancing the chain tail.

Signing is injected via the ``signer`` callable (``element -> signed_xml_str``)
so this layer carries no XML-DSig dependency: :mod:`compliance.signing` supplies
the XAdES signer once it lands. With no signer the record persists unsigned
(``signed=False``) — the chain/persistence semantics are identical.
"""
from django.db import transaction

from . import records
from .models import IssuerChain, VerifactuRecord
from .validation import validate_issuable

# Single-sourced in the package __init__ (the public surface); imported here at
# call time — services is itself imported lazily, after the app registry is ready.
from compliance import MODULE_VERSION


def _fecha_exp(invoice) -> str:
    """FechaExpedicionFactura in AEAT DD-MM-YYYY form."""
    return invoice.issue_date.strftime("%d-%m-%Y")


def _num_serie(invoice) -> str:
    """NumSerieFactura — the series prefix + assigned number."""
    return f"{invoice.series.prefix}{invoice.number}"


def _now_stamp() -> str:
    """FechaHoraHusoGenRegistro — ISO 8601 local time with offset."""
    from django.utils import timezone

    return timezone.localtime().isoformat(timespec="seconds")


def _lock_chain(issuer_nif: str) -> tuple[IssuerChain, VerifactuRecord | None]:
    """Row-lock the issuer's chain head and return (head, current tail record).

    ``get_or_create`` then a locked re-select serialises every generation for
    this issuer; the tail is the latest persisted record (authoritative over the
    denormalised ``head.last_huella``).
    """
    head, _ = IssuerChain.objects.get_or_create(issuer_nif=issuer_nif)
    head = IssuerChain.objects.select_for_update().get(pk=head.pk)
    tail = (
        VerifactuRecord.objects.filter(issuer_nif=issuer_nif)
        .order_by("-id")
        .first()
    )
    return head, tail


def generate_alta(invoice, *, issuer_nif, issuer_name, fecha_hora=None,
                  signer=None, tipo_factura="F1", tipo_rectificativa=None,
                  rectifies=None):
    """Validate, build, chain, (optionally) sign and persist an alta record.

    ``signer`` is an optional ``element -> signed_xml_str`` callable
    (:mod:`compliance.signing`). ``fecha_hora`` may be pinned for deterministic
    tests; it defaults to now. Returns the persisted
    :class:`~compliance.models.VerifactuRecord`.

    For a factura rectificativa (T-017, UC-004), pass ``tipo_factura`` in R1–R5,
    ``tipo_rectificativa`` ("S"/"I") and ``rectifies`` — the rectified invoice's
    prior alta record. The defaults produce an ordinary F1 alta unchanged.
    """
    validate_issuable(invoice, issuer_nif=issuer_nif, issuer_name=issuer_name)
    fecha_hora = fecha_hora or _now_stamp()
    num_serie = _num_serie(invoice)
    fecha_exp = _fecha_exp(invoice)
    totals = invoice.compute_totals()

    with transaction.atomic():
        head, prev = _lock_chain(issuer_nif)
        element, huella, cuota, importe = records.build_registro_alta(
            issuer_nif=issuer_nif,
            issuer_name=issuer_name,
            num_serie=num_serie,
            fecha_exp=fecha_exp,
            fecha_hora=fecha_hora,
            totals=totals,
            recipient_name=invoice.recipient_name,
            recipient_taxid=invoice.recipient_taxid,
            previous=prev,
            tipo_factura=tipo_factura,
            tipo_rectificativa=tipo_rectificativa,
            rectifies=rectifies,
        )
        signed = False
        xml = records.serialize(element)
        if signer is not None:
            xml = signer(element)
            signed = True

        record = VerifactuRecord.objects.create(
            invoice=invoice,
            record_type=VerifactuRecord.ALTA,
            issuer_nif=issuer_nif,
            issuer_name=issuer_name,
            num_serie=num_serie,
            fecha_expedicion=fecha_exp,
            tipo_factura=tipo_factura,
            cuota_total=cuota,
            importe_total=importe,
            fecha_hora_gen=fecha_hora,
            huella=huella,
            previous_record=prev,
            previous_huella=prev.huella if prev else "",
            xml=xml,
            signed=signed,
            module_version=MODULE_VERSION,
        )
        head.last_huella = huella
        head.save(update_fields=["last_huella"])
    return record


def generate_anulacion(original, *, issuer_name=None, fecha_hora=None,
                       signer=None):
    """Generate a chained, signed annulment for an existing alta ``record``.

    Voids ``original`` (a :class:`~compliance.models.VerifactuRecord` of type
    ``alta``) by emitting a ``RegistroAnulacion`` that references its IDFactura
    and chains on the issuer's current tail (UC-005). Returns the persisted
    annulment record.
    """
    issuer_nif = original.issuer_nif
    issuer_name = issuer_name or original.issuer_name
    fecha_hora = fecha_hora or _now_stamp()

    with transaction.atomic():
        head, prev = _lock_chain(issuer_nif)
        element, huella = records.build_registro_anulacion(
            issuer_nif=issuer_nif,
            issuer_name=issuer_name,
            num_serie=original.num_serie,
            fecha_exp=original.fecha_expedicion,
            fecha_hora=fecha_hora,
            previous=prev,
        )
        signed = False
        xml = records.serialize(element)
        if signer is not None:
            xml = signer(element)
            signed = True

        record = VerifactuRecord.objects.create(
            invoice=original.invoice,
            record_type=VerifactuRecord.ANULACION,
            issuer_nif=issuer_nif,
            issuer_name=issuer_name,
            num_serie=original.num_serie,
            fecha_expedicion=original.fecha_expedicion,
            tipo_factura=original.tipo_factura,
            cuota_total=original.cuota_total,
            importe_total=original.importe_total,
            fecha_hora_gen=fecha_hora,
            huella=huella,
            previous_record=prev,
            previous_huella=prev.huella if prev else "",
            xml=xml,
            signed=signed,
            module_version=MODULE_VERSION,
        )
        head.last_huella = huella
        head.save(update_fields=["last_huella"])
    return record
