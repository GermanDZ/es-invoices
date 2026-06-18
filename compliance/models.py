"""Persistence for the compliance/Verifactu module (T-013 Operation 1).

A :class:`VerifactuRecord` is the legally-meaningful record generated from an
issued :class:`invoicing.models.Invoice` — an ``alta`` (registration) or an
``anulacion`` (annulment). Records form an **append-only, per-issuer hash chain**
(``huella`` of each record folds in the previous record's ``huella``), so the
sequence is tamper-evident: altering or dropping any record breaks every chain
link after it (AD-2, Q-1).

This module owns the persistence only; the rules that *fill* these fields live in
:mod:`compliance.records` (XML + ``huella``), :mod:`compliance.validation`
(legal-field gate) and :mod:`compliance.services` (the transactional chain).
Nothing here submits to the AEAT — that is the T-014 adapter behind AD-3.
"""
from django.db import models

# The values the huella concatenation and the chain-tail lock are computed over
# are stored as-generated (strings/Decimals exactly as serialised), so a stored
# record reproduces its own huella byte-for-byte — never recomputed from a live
# re-read of the (mutable-elsewhere) source rows.


class IssuerChain(models.Model):
    """Per-issuer serialization point for the hash chain (one row per NIF).

    The chain spans **all** of an issuer's numbering series, so — unlike T-012's
    per-``Series`` high-water lock — the serialization row is keyed on the issuer
    NIF. :func:`compliance.services.generate_alta` row-locks this
    (``select_for_update``) for the duration of a generation so two concurrent
    records cannot both read the same chain tail and fork it (AD-6/Q-1). The
    denormalised ``last_huella`` mirrors the tail for cheap reads; the authoritative
    tail is still the latest :class:`VerifactuRecord` for the issuer.
    """

    issuer_nif = models.CharField(max_length=16, unique=True)
    last_huella = models.CharField(max_length=64, blank=True, default="")

    def __str__(self):
        return f"chain[{self.issuer_nif}] @ {self.last_huella[:8] or '∅'}"


class VerifactuRecord(models.Model):
    """One Verifactu record (alta | anulacion) in an issuer's hash chain."""

    ALTA = "alta"
    ANULACION = "anulacion"
    RECORD_TYPES = [(ALTA, "Alta"), (ANULACION, "Anulación")]

    invoice = models.ForeignKey(
        "invoicing.Invoice",
        on_delete=models.PROTECT,
        related_name="verifactu_records",
    )
    record_type = models.CharField(max_length=10, choices=RECORD_TYPES)

    # Chain key + record identity (the huella input fields, stored verbatim) ---
    issuer_nif = models.CharField(max_length=16)
    num_serie = models.CharField(max_length=64)
    fecha_expedicion = models.CharField(max_length=10)  # FechaExpedicionFactura
    tipo_factura = models.CharField(max_length=4, default="F1")
    cuota_total = models.DecimalField(max_digits=12, decimal_places=2)
    importe_total = models.DecimalField(max_digits=12, decimal_places=2)
    # FechaHoraHusoGenRegistro — ISO 8601 with offset; stored as the exact string
    # folded into the huella so the hash is reproducible.
    fecha_hora_gen = models.CharField(max_length=32)

    # Hash chain ---------------------------------------------------------------
    huella = models.CharField(max_length=64)
    previous_record = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="next_records",
    )
    previous_huella = models.CharField(max_length=64, blank=True, default="")

    # Generated payload --------------------------------------------------------
    xml = models.TextField()
    signed = models.BooleanField(default=False)
    module_version = models.CharField(max_length=16)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # One record of a given kind per (issuer, invoice identity): an alta
            # and its anulacion share num_serie but differ by type.
            models.UniqueConstraint(
                fields=["issuer_nif", "num_serie", "record_type"],
                name="uniq_verifactu_issuer_numserie_type",
            )
        ]
        indexes = [
            # The chain-tail lookup (latest record for an issuer) — see
            # compliance.services._lock_chain_tail.
            models.Index(fields=["issuer_nif", "id"], name="idx_verifactu_chain"),
        ]

    def __str__(self):
        return f"{self.record_type} {self.num_serie} ({self.huella[:8]}…)"
