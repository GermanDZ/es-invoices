---
type: pricing-validation
id: PRICE-001
title: FacturaSimple — Willingness-to-Pay & Pricing Validation
status: draft-pending-founder-decision
traces-from: [VIS-001, R-04]
relates-to: [SCOPE-001]
owner-role: analyst (decision: product-owner)
last-updated: 2026-06-15
---

# Willingness-to-Pay & Pricing Validation — FacturaSimple

> **Purpose.** Close the two open business items the project has carried since
> Inception — the **paying-accounts target** (`docs/vision.md` §5, marked *TODO*)
> and the **pricing decision** (`docs/scope.md` §6 open item) — and reduce
> **R-04** (low adoption / weak willingness to pay), the highest live *business*
> exposure in `docs/risk-list.md`.
>
> **What this document is.** An evidence-based **pricing hypothesis plus a
> validation plan** — not a finished market study. The analyst can supply
> competitor benchmarks, candidate models, and funnel math; only the founder can
> supply the deciding inputs (the actual price, whether to run a free tier, and
> the paying-accounts target). Those are raised separately in
> `docs/input-requests/2026-06-15-pricing-and-paying-target.md`. Real
> willingness-to-pay numbers come only from target users — §6 defines how we
> get them. Treat every figure here as a **directional benchmark to be
> validated, not a measured fact.**

## 1. What this closes

| Open item | Source | How this document addresses it |
|---|---|---|
| Active paying-accounts target = **TODO** | Vision §5 (metric 5) | §5 proposes a 12-month target *range* + the funnel math behind it; the founder sets the number (input-request Q4). |
| Pricing not yet decided | Scope §6 open item | §3–§4 give a price band + candidate models; the founder decides (input-request Q1–Q3). |
| R-04 mitigation = "validate WTP before heavy build" | Risk list R-04 | §6 is the concrete, verifiable validation plan that discharges R-04's mitigation. |

## 2. Market & demand context

**The demand catalyst is regulatory, and its timing is the single biggest swing
factor.** The Verifactu / *Ley Antifraude* mandate forces every Spanish
autónomo onto compliant invoicing software within a defined window — exactly the
market-wide, time-bound shift the Vision (§8) is built around.

- **Deadline (as of 2026-06-15) is uncertain and must be tracked.** Under **RD
  254/2025** the dates were **1 Jan 2026** (sociedades) and **1 Jul 2026** (the
  rest — autónomos, atribución de rentas, IRNR con EP). However, a **2 Dec 2025
  government announcement proposed a further prórroga to 1 Jan 2027 (personas
  jurídicas) and 1 Jul 2027 (autónomos)**. So the autónomo compliance wall is
  either **~2 weeks away or ~12 months away** depending on whether that prórroga
  is enacted. *(This is the same regulatory-timing exposure as R-01; confirm the
  current legal deadline before committing the go-to-market calendar.)*
- **Why it matters for pricing.** A near deadline = urgent, deadline-driven
  demand (buyers compare against the cost of a *fine*, not against a spreadsheet)
  → supports a clean paid model and a faster paying-accounts ramp. A deferred
  deadline = softer near-term urgency → strengthens the case for a free/low entry
  tier to capture users early and convert them as their deadline approaches.
- **Segment size.** Spain has on the order of ~3 million autónomos plus a large
  base of micro-pymes — a large addressable pool, *but* the target sub-segment is
  the price-sensitive "I just need to invoice legally" niche the Vision picks out
  (not the full accounting-suite market). *(Order-of-magnitude only — size the
  serviceable segment properly during validation.)*
- **Price sensitivity (R-04 core).** This segment is genuinely price-sensitive:
  the realistic alternatives are (a) free spreadsheets/Word — *now non-compliant
  under Verifactu, which is the wedge*; (b) leaning on their **gestor**; or (c) a
  cheaper/established competitor. Pricing has to beat "do nothing" on
  *compliance fear* and beat competitors on *simplicity + price*.

## 3. Competitor pricing benchmark

Spanish autónomo-focused invoicing tools cluster in a **~6–15 €/month** band for
entry plans, with broader suites reaching higher. Snapshot (≈ mid-2026; **verify
before quoting — vendor prices and Verifactu-tier packaging change frequently,
and annual-billing headline prices understate monthly cost**):

| Tool | Entry price (≈/mo) | Notes |
|---|---|---|
| Anfix | from ~2.49 (annual) → up to ~41.66 | Wide range; low headline is annual-billing teaser. |
| FacturaDirecta | ~8.33 | Autónomo/small-pyme focus, gestoría integration, Verifactu-compatible. |
| Billin | ~9 (range ~6.6–20) | Explicitly Ley Antifraude / Verifactu adapted. |
| Quipu | ~13 (basic) | Broader: invoicing + tesorería + automation. |
| Holded / Sage / Declarando | higher / suite-priced | Broad accounting/ERP suites — the "over-featured, over-priced" comparators the Vision §1 calls out. |

**Read-out:** the competitive entry band is roughly **6–13 €/month**. A
focused, compliance-first single product can credibly position **at or slightly
below the low end** (simplicity + price as the wedge, per R-05 mitigation) — *or*
lead with a free entry tier the broad suites generally don't offer for the
"just invoicing" use case.

## 4. Willingness-to-pay hypothesis & candidate models

### 4.1 WTP hypothesis
For the target niche, the credible monthly WTP anchor is **"clearly less than a
gestor charges, and trivially less than a Verifactu fine"** — i.e. a small,
easy-yes monthly figure. Hypothesised acceptable band: **~5–10 €/month**, with a
psychological sweet spot around **~6–8 €/month** for a single, no-accounting-needed
compliant-invoicing plan. *(Hypothesis — to be tested per §6, not a finding.)*

### 4.2 Candidate pricing models

| Model | Shape | Pros | Cons / risks |
|---|---|---|---|
| **A. Single flat plan** | One paid tier, ~6–9 €/mo (monthly + discounted annual) | Simplest; matches "one job done well"; predictable revenue; fastest to ship | No free on-ramp; full price-sensitivity friction at signup (R-04); weaker if deadline defers |
| **B. Freemium** | Free tier (capped invoices/features) + paid ~7–10 €/mo | Lowest adoption friction; captures users *before* their deadline; land-and-expand; strong if deadline defers | Free-tier support cost; conversion risk (free users may never pay); must avoid giving away the compliance core for free |
| **C. Usage-tiered** | 2–3 tiers by invoice volume / features | Captures higher-volume pymes; price discrimination | More complexity; cuts against the "simple" promise; harder to communicate the 5-min value |

### 4.3 Analyst recommendation (hypothesis for the founder to confirm/override)
Lead with **Model A (single flat plan, ~7 €/month, with a discounted annual
price) plus a time-boxed free trial** — it best fits "one job, done well" and a
near deadline. **Add a capped free tier (Model B) only if the deadline defers**
to 2027, where capturing users early and converting them at their deadline
becomes the stronger play. Keep tiering (Model C) out of v1 — it taxes the
simplicity that is the differentiator. **A trial (not a permanent free tier) is
the lower-regret default**: it tests conversion without standing free-tier cost.

## 5. Paying-accounts target (Vision §5 metric 5)

The target should be derived from the funnel, not picked arbitrarily. The chain:

```
paying accounts (12 mo) = signups × activation rate × trial→paid conversion
```

- **Activation rate** already has a Vision target: **≥ 50%** (issue ≥1 invoice in
  week 1).
- **Trial→paid conversion** is the unknown R-04 hinges on; SaaS self-serve trials
  commonly convert in a wide range — *to be measured in beta (§6)*.
- **Signups** depend on the deadline timing (§2) and acquisition spend (out of
  scope here).

**Illustrative (NOT a commitment — shows the shape so the founder can set the
number):** if v1 reaches ~2,000 signups in year one, with 50% activation and a
~20–30% trial→paid conversion, that implies **~200–300 paying accounts in 12
months**. A reasonable **target band to ratify is ~150–400 paying accounts by
month 12**, to be narrowed once the deadline (§2) and a beta conversion read
(§6) are known. *The founder sets the committed number (input-request Q4).*

## 6. Validation plan (this is the R-04 mitigation — verifiable)

R-04's mitigation is *"validate willingness-to-pay with target users before heavy
build."* Concrete, checkable steps:

1. **Price-test landing page (pre/early build).** Publish the value prop with a
   stated price (or 2 price variants) and a "notify me / reserve" CTA; measure
   click-through and email capture per price. *Verifiable:* a live page + a dated
   results note.
2. **Target-user interviews (n ≈ 8–12 autónomos).** Test the compliance-fear
   value prop and the ~5–10 €/mo band directly (e.g. Van Westendorp-style price
   questions). *Verifiable:* interview notes + a price-sensitivity summary.
3. **Beta cohort with real pricing.** Run the trial→paid flow with actual money
   on a small beta; this is the only true WTP signal. *Verifiable:* a beta
   cohort with a measured trial→paid conversion number.
4. **Instrument the funnel from day one** (already a Vision metric + R-04
   mitigation): time-to-first-invoice, activation rate, trial→paid. *Verifiable:*
   instrumentation live before GA.
5. **Decision gate.** If beta trial→paid is materially below the §5 assumption,
   revisit the model (e.g. switch A→B, adjust price) *before* scaling spend.

**Owner:** Product Owner. **Addresses:** R-04 (and feeds R-05 positioning).

## 7. Open decisions for the founder

These are raised in `docs/input-requests/2026-06-15-pricing-and-paying-target.md`
(only the founder can supply them):

- **Q1** — Pricing model: A (single flat) / B (freemium) / C (tiered).
- **Q2** — Price point / band for the paid plan.
- **Q3** — Free trial vs. permanent free tier (and what it includes — must not
  give the compliance core away).
- **Q4** — Committed 12-month paying-accounts target (closes Vision §5).
- **Q5** — Any steering input: current legal deadline assumption (§2), existing
  market data, or a target sub-segment detail.

Once answered, a future `/openup-next` cycle folds the decisions into Vision §5
(set the target), scope.md §6 (mark pricing decided), and finalizes this
document `status: agreed`.

## 8. Traceability & status

- **Traces from:** VIS-001 (§5 metric 5; §6 WTP assumption), R-04 (risk list).
- **Relates to:** SCOPE-001 §6 (pricing open item), R-01/R-05 (deadline timing,
  competitive positioning).
- **Status:** `draft-pending-founder-decision` — analysis complete; the four
  decisions in §7 are pending founder input. Lane **suspended** on that
  input-request; resumes via `/openup-next`.

---

*Self-critique: the load-bearing weakness is that all WTP figures are benchmark
+ hypothesis, not measured — §6 exists precisely to convert them to evidence
before heavy spend, which is what discharges R-04 rather than merely restating
it. The second weakness is deadline uncertainty (§2): the prórroga question
swings both the urgency of demand and the free-tier decision, so it is flagged
as a founder steering input (Q5) rather than silently assumed. Authored in
Elaboration (T-009, analyst hat).*
