"""Calculation tests (T-012 requirements 1–3) — pure, no database."""
from collections import namedtuple
from decimal import Decimal

from django.test import SimpleTestCase

from invoicing import calc

Line = namedtuple("Line", "quantity unit_price iva_rate")


def D(x):
    return Decimal(str(x))


class ComputeTotalsTests(SimpleTestCase):
    def test_multi_rate_totals_to_the_cent(self):
        """Req 1: two lines at 21% + one at 10% → exact Decimal totals."""
        lines = [
            Line(D(2), D("100.00"), D(21)),   # 200.00 @ 21%
            Line(D(1), D("50.00"), D(21)),    # 50.00  @ 21%
            Line(D(3), D("10.00"), D(10)),    # 30.00  @ 10%
        ]
        t = calc.compute_totals(lines)
        self.assertEqual(t.taxable_base, D("280.00"))
        self.assertEqual(t.iva_total, D("55.50"))      # 52.50 + 3.00
        self.assertEqual(t.irpf_retention, D("0.00"))
        self.assertEqual(t.grand_total, D("335.50"))
        # No float anywhere — every total is a Decimal.
        for value in (t.taxable_base, t.iva_total, t.irpf_retention, t.grand_total):
            self.assertIsInstance(value, Decimal)

    def test_rate_grouping_with_exempt(self):
        """Req 2: 21% / 10% / 0%-exempt each report their own base + IVA."""
        lines = [
            Line(D(1), D("100.00"), D(21)),
            Line(D(1), D("100.00"), D(10)),
            Line(D(1), D("100.00"), D(0)),   # exempt
        ]
        t = calc.compute_totals(lines)
        groups = {g.rate: g for g in t.groups}
        self.assertEqual(groups[D(21)].iva, D("21.00"))
        self.assertEqual(groups[D(10)].iva, D("10.00"))
        self.assertEqual(groups[D(0)].iva, D("0.00"))   # exempt adds nothing
        self.assertEqual(t.iva_total, D("31.00"))
        # Invoice IVA equals the sum of the independently-rounded per-group IVAs.
        self.assertEqual(t.iva_total, sum(g.iva for g in t.groups))

    def test_per_group_rounding_is_independent(self):
        """Req 2: each group's IVA is rounded on its own base (not per line)."""
        lines = [Line(D(1), D("100.10"), D(21))]   # 100.10 * 0.21 = 21.021
        t = calc.compute_totals(lines)
        self.assertEqual(t.taxable_base, D("100.10"))
        self.assertEqual(t.iva_total, D("21.02"))   # ROUND_HALF_UP of 21.021

    def test_irpf_applied_when_configured(self):
        """Req 3: 15% IRPF retention subtracted from the grand total."""
        lines = [Line(D(1), D("1000.00"), D(21))]
        t = calc.compute_totals(lines, irpf_rate=D(15))
        self.assertEqual(t.taxable_base, D("1000.00"))
        self.assertEqual(t.iva_total, D("210.00"))
        self.assertEqual(t.irpf_retention, D("150.00"))
        self.assertEqual(t.grand_total, D("1060.00"))   # 1000 + 210 - 150

    def test_irpf_omitted_when_not_subject(self):
        """Req 3 / alt-flow 3a: no retention when IRPF rate is 0."""
        lines = [Line(D(1), D("1000.00"), D(21))]
        t = calc.compute_totals(lines, irpf_rate=D(0))
        self.assertEqual(t.irpf_retention, D("0.00"))
        self.assertEqual(t.grand_total, D("1210.00"))
