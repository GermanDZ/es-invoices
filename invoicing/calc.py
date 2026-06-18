"""Pure invoice arithmetic (T-012 Operation 2) — no ORM, no I/O.

All money is :class:`~decimal.Decimal`; **float never enters the money path**
(R-02, AD-6/Q-1). The Spanish rule is to compute and round IVA **per rate
group**: line amounts at the same IVA rate are summed into a taxable base, that
base is rounded to cents, and the group's IVA is rounded independently before
the per-group IVAs are summed into the invoice total. IRPF is a single
invoice-level retention on the whole taxable base (UC-001 step 3 / alt-flow 3a).

Keeping this isolated and ORM-free makes the compliance arithmetic unit-testable
without a database — the model layer (:mod:`invoicing.models`) and the issuance
service (:mod:`invoicing.services`) call in here for every total they persist.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")

# Spanish IVA rates in force (percentage points). 0 = exempt / not subject.
IVA_RATES = (Decimal("21"), Decimal("10"), Decimal("4"), Decimal("0"))


def money(value) -> Decimal:
    """Quantise to 2 decimals, ROUND_HALF_UP (the rounding the AEAT expects)."""
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class RateGroup:
    """One IVA-rate bucket: its rounded taxable base and its rounded IVA."""

    rate: Decimal
    base: Decimal
    iva: Decimal


@dataclass(frozen=True)
class InvoiceTotals:
    taxable_base: Decimal
    iva_total: Decimal
    irpf_retention: Decimal
    grand_total: Decimal
    groups: tuple = field(default_factory=tuple)


def line_amount(quantity, unit_price) -> Decimal:
    """Quantity × unit price, rounded to cents."""
    return money(Decimal(quantity) * Decimal(unit_price))


def compute_totals(lines, irpf_rate=Decimal("0")) -> InvoiceTotals:
    """Compute invoice totals from ``lines`` and an invoice-level IRPF rate.

    ``lines`` is any iterable of objects exposing ``quantity``, ``unit_price``
    and ``iva_rate`` (Decimals) — model instances or plain rows both work.
    IVA is grouped and rounded per rate; IRPF (percentage of the whole taxable
    base) is omitted when ``irpf_rate`` is 0.
    """
    irpf_rate = Decimal(irpf_rate)
    bases: dict = {}
    for line in lines:
        rate = Decimal(line.iva_rate)
        bases[rate] = bases.get(rate, Decimal("0")) + line_amount(
            line.quantity, line.unit_price
        )

    groups = []
    taxable_base = Decimal("0")
    iva_total = Decimal("0")
    # Sort high-rate-first for a stable, readable breakdown.
    for rate in sorted(bases, reverse=True):
        base = money(bases[rate])
        iva = money(base * rate / Decimal("100"))
        groups.append(RateGroup(rate=rate, base=base, iva=iva))
        taxable_base += base
        iva_total += iva

    taxable_base = money(taxable_base)
    iva_total = money(iva_total)
    irpf_retention = money(taxable_base * irpf_rate / Decimal("100"))
    grand_total = money(taxable_base + iva_total - irpf_retention)

    return InvoiceTotals(
        taxable_base=taxable_base,
        iva_total=iva_total,
        irpf_retention=irpf_retention,
        grand_total=grand_total,
        groups=tuple(groups),
    )
