---
title: "Pricing model + paying-accounts target (R-04 / Vision §5)"
created: "2026-06-15T14:45:00Z"
created_by: "openup-next (T-009, analyst hat)"
status: pending
related_task: "T-009"
run_id: "T-009-iter8"
---

# Input Request — Pricing Decision & Paying-Accounts Target

## Context

**Iteration 8 (Elaboration), task T-009** — willingness-to-pay / pricing
validation. Addresses **R-04** (low adoption / weak willingness to pay — the
highest live *business* exposure) and closes two items the project has carried
since Inception: the **paying-accounts target** (Vision §5 metric 5, marked
*TODO*) and the **pricing decision** (scope §6 open item).

The analysis is **done and persisted** in `docs/pricing-validation.md`
(PRICE-001). Headline findings:

- **Competitor entry band ≈ 6–13 €/month** (Anfix, FacturaDirecta ~8.33, Billin
  ~9, Quipu ~13; broad suites higher). A focused compliance-first product can sit
  **at or just below the low end** on a simplicity+price wedge.
- **WTP hypothesis ≈ 5–10 €/mo**, sweet spot ~6–8 €/mo — *"clearly less than a
  gestor, trivially less than a Verifactu fine."* (Hypothesis, not measured.)
- **Deadline timing is the big swing.** RD 254/2025 set the autónomo Verifactu
  date at **1 Jul 2026**, but a **2 Dec 2025 announcement proposed deferring it
  to 1 Jul 2027**. Which governs is **unconfirmed as of today** and changes the
  pricing play (near deadline → paid + trial; deferred → capture early with a
  free tier).
- **Analyst recommendation:** single flat plan **~7 €/mo (+ discounted annual)
  with a free trial**; add a capped free tier **only if** the deadline defers;
  keep tiering out of v1.

This is brought to you (not decided by the analyst) because it sets your
**revenue model, cash/runway, and the committed growth target** — the same
"only the founder can supply the deciding input" reason AD-3/AD-5/AD-6 were yours.

## Questions

### Q1: Pricing model
**Type**: multiple-choice
**Accepts**: one option

- [ ] `A — Single flat plan + free trial (recommended)` - One paid tier (~7 €/mo
      + discounted annual), time-boxed trial, no permanent free tier. Simplest;
      fits "one job done well" and a near deadline.
- [ ] `B — Freemium` - Capped free tier + paid ~7–10 €/mo. Lowest friction;
      best if the deadline defers to 2027 (capture users early, convert later).
- [ ] `C — Usage-tiered` - 2–3 tiers by volume/features. Captures higher-volume
      pymes but adds complexity (cuts against the simplicity differentiator).

### Q2: Price point for the paid plan
**Type**: text
**Example**: "7 €/mo, 70 €/yr", "9.99 €/mo", "match Billin at ~9 €", "go lower — 5 €"

What monthly (and annual, if any) price for the paid plan?

**Answer**:

### Q3: Free trial vs. permanent free tier
**Type**: multiple-choice
**Accepts**: one option

- [ ] `Free trial only (recommended)` - e.g. 14–30 day trial of the full
      product; no standing free-tier cost. Tests conversion cleanly.
- [ ] `Permanent capped free tier` - e.g. N invoices/month free. Lower adoption
      friction; standing support cost; must NOT give the compliance core away.
- [ ] `Both` - Trial now, add a capped free tier later if the deadline defers.

If a free tier, what should it include / cap?

**Answer**:

### Q4: 12-month paying-accounts target (closes Vision §5)
**Type**: text
**Example**: "250 paying accounts by month 12", "150–400 band, narrow after beta", "I want a number after the beta read"

The funnel math (signups × ≥50% activation × trial→paid) suggests an
illustrative **~150–400 paying accounts by month 12**. What number (or band)
should the Vision commit to?

**Answer**:

### Q5: Steering input (deadline, data, segment)
**Type**: text
**Example**: "Assume the 2027 prórroga holds", "Deadline is firm 1 Jul 2026", "I already have a waitlist of N", "Target sub-segment is X"

Optional — your current **legal-deadline assumption** (this changes Q1/Q3), any
existing market/waitlist data, or a target sub-segment detail that should steer
the choice.

**Answer**:

## Instructions for Respondent

1. Fill in the **Answer** section under each question (tick one box for the
   multiple-choice ones).
2. Change `status: pending` → `status: answered` in the frontmatter.
3. Save the file.
4. Re-run `/openup-next` — it will resume T-009, fold your decisions into
   **Vision §5** (set the paying-accounts target) and **scope §6** (mark pricing
   decided), finalize `docs/pricing-validation.md` (`status: agreed`), and
   complete the task.
