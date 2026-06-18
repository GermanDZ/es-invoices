# T-012 — Design notes & completion verification

## In-flight decisions

- **DD1 — Pure `calc.py`, ORM-free.** The IVA/IRPF arithmetic (the R-02 surface)
  lives in `invoicing/calc.py` as pure `Decimal` functions with no Django imports,
  so it is unit-testable without a database. Models/services call into it.
- **DD2 — Per-rate-group rounding.** Taxable base is grouped by IVA rate; each
  group's IVA is rounded (`ROUND_HALF_UP`) independently, then summed — the AEAT
  rule. IRPF is a single invoice-level retention on the whole base.
- **DD3 — Numbering = `select_for_update` + unique constraint + bounded retry.**
  `services.issue_invoice` opens one `transaction.atomic()`, row-locks the series
  (real lock on PostgreSQL/AD-6, no-op on the SQLite test fallback), assigns
  `last_number + 1`, advances the high-water mark. `(series, number)` is unique, and
  a bounded retry catches the lost-update race the lock-less SQLite path can produce
  — the loser rolls back, re-reads the advanced mark, and gets the next number. Net:
  gap-free + duplicate-free on either backend.
- **DD4 — Recipient as denormalised snapshot.** No FK to a Client (that is T-015);
  the invoice carries `recipient_name/taxid/address` so issued records are stable.
- **DD5 — Immutability at the model layer.** `Invoice.save` rejects changes to
  `series_id/number/issue_date` once `issued` is true (requirement 6).
- **DD6 — Concurrency test is Postgres-gated.** A true threaded race needs real row
  locks; `ConcurrentIssuanceTests` is `@skipUnlessDBFeature("has_select_for_update")`
  so it runs on production-like PostgreSQL and is skipped on the SQLite suite, where
  the deterministic retry test covers the lock-less path. No silent gap in coverage —
  the skip is documented and the mechanism is tested both ways.

## Completion verification — requirements vs the actual diff (skill step 1a)

Graded against `git diff` + the green `invoicing` test suite (15 tests, 1 Postgres-only skip).

- ✅ **Req 1** (line items + Decimal totals, per-group rounding) — `invoicing/calc.py`
  `compute_totals`; `test_calc.test_multi_rate_totals_to_the_cent` asserts 280.00 /
  55.50 / 335.50 to the cent, and that every total is a `Decimal`.
- ✅ **Req 2** (per-line IVA, grouped + independently rounded, no float) — `calc.py`
  rate-group loop; `test_rate_grouping_with_exempt` (exempt adds 0; total == Σ group
  IVAs) and `test_per_group_rounding_is_independent` (100.10 @21% → 21.02).
- ✅ **Req 3** (IRPF invoice-level, omitted when 0) — `calc.py` irpf branch;
  `test_irpf_applied_when_configured` (15% → 150.00, grand 1060.00) and
  `test_irpf_omitted_when_not_subject`.
- ✅ **Req 4** (atomic gap-free numbering, unique, concurrency-safe) —
  `services.issue_invoice` + `Invoice` unique constraint; `test_sequential...`
  ([1,2,3], high-water 3), `test_unique_constraint_blocks_a_duplicate_number`
  (IntegrityError), `test_retry_resolves_a_lost_update...` (no gap/dup), and the
  Postgres-gated `ConcurrentIssuanceTests` for the true race.
- ✅ **Req 5** (validation blocks issue without consuming a number) —
  `services._validate_issuable` inside `atomic`; `test_no_line_items...` and
  `test_missing_mandatory_field_rolls_back_and_number_not_consumed` (next valid issue
  still gets 1).
- ✅ **Req 6** (issued invoice immutable on identity; snapshot + totals persisted) —
  `Invoice.save` guard; `test_immutability` (number/issue_date raise; snapshot + totals
  readable).

**Result:** all 6 requirements ✅ against the diff. No ❌.

## Success-measure instrumentation (skill step 1b)

**n/a — argued.** The spec's `## Success Measures` is an argued `n/a`: internal core
with no user-facing funnel/billing surface live at this phase. The falsifiable,
deterministic expectation (zero numbering gaps/duplicates and exact IVA/IRPF totals)
is read back **in CI on every run** via the `invoicing` suite, not on a release date.
Revisit when issuance ships to beta and a "successful-issue rate" becomes measurable.

## Rollout

Not flagged (`n/a` — net-new domain code, unreleased; no flag-removal task to enqueue).
