---
type: vision
id: VIS-001
title: FacturaSimple
status: approved
owner-role: analyst
---

# Vision: FacturaSimple

> Simple, compliant electronic invoicing for Spanish autónomos and very small businesses.

## 1. Problem Statement

Spain's self-employed (autónomos) and very small businesses (pymes) are legally
required to issue invoices that meet a growing list of fiscal and anti-fraud
requirements — sequential numbering, correct IVA/IRPF handling, mandatory legal
fields, and, with the **Verifactu / Ley Crea y Crece** rollout, tamper-evident
records that can be reported to the AEAT. For a one-person business this is a
real burden:

- **The compliance rules are confusing and the stakes are rising.** Most
  autónomos are not accountants. They struggle to know what makes an invoice
  legal, and the Verifactu mandate raises the cost of getting it wrong.
- **Existing tools are too complex and/or too costly.** The established options
  (Holded, Sage, Quaderno, Declarando, and similar suites) are built as broad
  accounting/ERP platforms. For someone who simply needs to issue a handful of
  compliant invoices a month, they are over-featured, over-priced, and
  intimidating.

The result is that many autónomos fall back on spreadsheets or Word templates
that are error-prone and will not satisfy the new compliance regime — or they
pay for far more software than they need.

## 2. Proposed Solution

FacturaSimple is a focused web application that lets an autónomo or very small
pyme create and send a **legally compliant Spanish invoice in minutes**, with no
accounting knowledge required.

What it does:

- Manage clients and issue invoices with correct sequential numbering, IVA, and
  IRPF retentions.
- Produce a clean PDF and send it by email.
- Generate Verifactu-compliant records and submit them to the AEAT.

What makes it different — **compliance-first / Verifactu-native**: rather than
bolting compliance onto a general accounting suite, FacturaSimple is built around
staying legal in Spain. The user never has to understand Verifactu; the product
guarantees that every invoice they issue is correct and reportable. Simplicity is
the second pillar — the entire experience is designed so a non-accountant gets to
a valid, sent invoice as fast as possible.

## 3. Stakeholders and Users

| Stakeholder | Role | Primary need | Success looks like |
|---|---|---|---|
| **Autónomo (independent contractor)** | Primary end user | Issue compliant invoices fast, without fiscal expertise; stay legal under Verifactu | Sends a valid invoice in minutes; never worries about AEAT compliance |
| **Very small pyme (micro-business)** | Primary end user | Same, plus light multi-client/recurring billing | Reliable monthly invoicing without an accounting hire |
| **Gestor / accountant** (the user's advisor) | Indirect stakeholder | Clean, correct, exportable records | Receives well-formed data; fewer corrections needed |
| **Founder / Product Owner** (solo founder) | Sponsor & operator | A lean, compliant product that acquires and retains paying users | Growing base of active paying accounts; sustainable to operate |
| **AEAT (tax authority)** | External / regulatory | Records submitted per Verifactu spec | Submissions accepted on first try |

## 4. Key Features / Scope

**In scope for the first release:**

1. Client/contact management.
2. Invoice creation with IVA and IRPF calculation, mandatory legal fields, and
   sequential numbering.
3. PDF generation and send-by-email.
4. Verifactu-compliant record generation and AEAT submission.
5. Basic invoice status tracking (issued / sent).

**Out of scope for v1 (future):**

- Quotes/estimates (presupuestos) and recurring/subscription invoicing.
- Expense tracking and IVA/IRPF quarterly summaries.
- Full accountant collaboration / advanced exports.
- Online payment collection.
- Markets outside Spain.

Features are intentionally narrow: do invoicing + compliance extremely well
before expanding.

## 5. Success Metrics

Primary (north-star):

1. **Time to first invoice** — median minutes from signup to a legally valid
   invoice sent. Target: **under 5 minutes**.

Supporting:

2. **Activation rate** — % of signups who issue ≥ 1 invoice in their first week.
   Target: **≥ 50%**.
3. **Verifactu success rate** — % of invoices accepted by the AEAT on first
   submission. Target: **≥ 99%**.
4. **3-month retention** — % of users still issuing invoices after three months.
   Target: **≥ 40%**.
5. **Active paying accounts** — paying autónomos/pymes within 12 months of
   launch. Target: TODO (set with product owner once pricing is decided).

## 6. Constraints and Assumptions

**Constraints:**

- **Spain-only legal scope.** Spanish-language UI, EUR, AEAT integration. This is
  not a generic international invoicer; the legal model is Spain-specific.
- **Data protection (RGPD/GDPR).** Handles personal and fiscal data; must comply
  with RGPD and keep data within the EU.
- **Small / bootstrapped team.** Limited budget and headcount. Scope must stay
  lean and favor build-vs-buy for non-core capabilities (email delivery,
  payments, e-invoice/AEAT gateway).
- **Tech stack: TODO** — to be decided in Elaboration.

**Assumptions (impact if violated):**

- The Verifactu/AEAT technical spec and deadlines are stable enough to build
  against. *If violated:* the core compliance engine needs rework and launch
  timing slips.
- Autónomos are willing to pay a modest subscription for guaranteed compliance +
  simplicity. *If violated:* the business model must change (e.g. free tier,
  different monetization).
- A compliant AEAT submission path is technically accessible to a small team
  (directly or via a gateway provider). *If violated:* v1 scope or build-vs-buy
  decisions change materially.

## 7. Risks Overview

| Risk | Type | Impact |
|---|---|---|
| **Crowded competitor market** | Market | Established players (Holded, Quaderno, Sage, Declarando) already serve this segment; FacturaSimple must win on simplicity + compliance focus or struggle to acquire users. |
| **Adoption / willingness to pay** | Business | Autónomos are price-sensitive and may stay with free spreadsheets or defer to their gestor; weak conversion threatens viability. |
| **Regulatory / Verifactu spec change** | Regulatory / Technical | AEAT spec or deadlines shift, forcing rework of the compliance core — the product's central value. *(Added because compliance is the product's core; see §6 assumption.)* |
| **Compliance correctness liability** | Technical / Trust | A bug that issues a non-compliant invoice damages trust and may carry legal consequences for users. |

A detailed risk list will be produced separately (roadmap task T-003).

## 8. Vision Alignment

The Verifactu / Ley Crea y Crece mandate is forcing every Spanish autónomo and
small business to adopt compliant electronic invoicing within a defined window —
a market-wide, time-bound shift in how millions of small businesses must invoice.
FacturaSimple exists to meet that moment for the segment the big suites under-serve:
people who need to **stay legal and get paid without becoming accountants**. Doing
one thing — compliant, effortless invoicing — exceptionally well is the strategy
against which all future scope decisions should be validated.

---

*Status: good-enough-for-Inception. Open TODOs: tech stack (Elaboration);
paying-accounts target (with product owner). Authored via guided Q&A (T-002).*
