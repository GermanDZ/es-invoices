---
type: scope
id: SCOPE-001
title: FacturaSimple — v1 Scope and Non-Goals
status: agreed
traces-from: [VIS-001]
owner-role: analyst
---

# Scope and Non-Goals — FacturaSimple v1

> Crystallizes the first-release boundary from the approved Vision (§4, §6) into
> an explicit, testable scope statement. This is the agreement against which every
> v1 feature request is validated: if it is not in **§2 In Scope**, it is out.

## 1. Scope Statement

FacturaSimple v1 lets a **single Spanish autónomo or micro-pyme** issue, send, and
keep legally compliant invoices — including the corrections the law requires — with
**zero accounting knowledge**, and guarantees each one is Verifactu-reportable to the
AEAT. The release does **one job** — compliant, effortless Spanish invoicing — and
deliberately excludes the broader accounting/ERP surface of competitor suites
(Vision §2, §8).

## 2. In Scope (v1)

| # | Capability | Traces to |
|---|---|---|
| S-1 | **Client/contact management** — create and maintain recipients (fiscal data). | REQ-003, UC-003 |
| S-2 | **Compliant invoice issuance** — mandatory legal fields, IVA + IRPF calculation, gap-free sequential numbering per series. | REQ-001, UC-001 |
| S-3 | **PDF generation + send by email** — produce a clean invoice PDF and deliver it to the recipient. | REQ-001 (Vision §4.3) |
| S-4 | **Verifactu record + AEAT submission** — generate the tamper-evident record per invoice, submit it, and store the accepted/rejected outcome. | REQ-002, UC-002 |
| S-5 | **Corrective / cancellation invoices** — issue *facturas rectificativas* (correct/reverse a valid invoice) and Verifactu *anulación* records (void a record sent in error), so a user can legally fix or void an issued invoice. | REQ-004, UC-004, UC-005 (D-1) |
| S-6 | **Basic invoice status tracking** — issued / sent state per invoice. | Vision §4.5 |

### Boundary clarifications (in scope, made explicit)

- **Recipients:** Spanish **B2B and B2C** — invoices to businesses/professionals
  (with NIF/CIF) *and* to final consumers (simplified-invoice rules where
  applicable). (D-2)
- **Account model:** **one user, one issuing business** per account. One fiscal
  identity, which may run **one or more numbering series**. (D-3)
- **Geography & locale:** Spain only — Spanish-language UI, EUR, AEAT integration
  (Vision §6 constraint).

## 3. Non-Goals (explicitly out of v1)

Out-of-scope items are listed so they cannot creep in unchallenged. Each may be
reconsidered in a future release; none is committed for v1.

| # | Non-goal | Why deferred |
|---|---|---|
| N-1 | Quotes/estimates (*presupuestos*) and recurring/subscription invoicing. | Vision §4 future list; not needed to issue a compliant invoice. |
| N-2 | Expense tracking and IVA/IRPF **quarterly summaries** (modelo 303/130 etc.). | Accounting surface; FacturaSimple is not a tax-filing tool. |
| N-3 | Full accountant/gestor collaboration and advanced exports. | Gestor is an *indirect* stakeholder (Vision §3); clean records suffice for v1. |
| N-4 | Online payment collection. | Out of the compliance core; build-vs-buy decision deferred. |
| N-5 | **Multi-user / team** accounts and **multiple businesses** per account. | Contradicts the single-user, single-business model (D-3); ERP territory. |
| N-6 | **Non-Spanish / international** invoicing (intra-EU reverse charge, foreign recipients, multi-currency, multi-language). | Spain-only legal scope is a hard constraint (Vision §6); the legal model is Spain-specific. |
| N-7 | Mobile native apps. | v1 is a focused web application (Vision §2). |

## 4. Scope Guardrails

- **Compliance is non-negotiable, breadth is.** Anything required to keep an issued
  invoice legal under Verifactu is in scope (this is why S-5 corrections are in);
  anything that merely broadens the product *beyond* invoicing is a non-goal.
- **The "5-minute" test (Vision §5).** A feature that does not help a non-accountant
  reach a valid, sent invoice faster is a candidate for cutting, not adding.
- **One job, done well.** New v1 requests are validated against §1; if accepting one
  would push FacturaSimple toward an accounting/ERP suite, it is rejected or deferred.

## 5. Boundary Decisions (with rationale)

These resolve ambiguities the Vision left implicit; agreed with the product owner
during T-005.

- **D-1 — Corrective/cancellation invoices are IN scope (S-5).** A "compliance-first"
  product that cannot legally correct or void a mistaken invoice breaks its own
  promise; Verifactu defines an annulment flow, so the capability is part of staying
  compliant, not an optional extra.
- **D-2 — Recipients: Spanish B2B *and* B2C.** Many autónomos invoice final consumers;
  excluding B2C would block a real, common use case. Simplified-invoice rules apply for
  consumer sales.
- **D-3 — Account model: single user, single business (one fiscal identity, ≥1 series).**
  Matches the lean, single-operator vision and keeps the data model simple; multi-user
  and multi-business are explicit non-goals (N-5).

## 6. Open Items (tracked, not blocking)

- ~~**REQ for corrections (S-5/D-1) not yet written.**~~ **Resolved (T-008, Elaboration):**
  added **REQ-004** (corrective + cancellation invoices) detailed by **UC-004** (factura
  rectificativa) and **UC-005** (Verifactu *anulación*); these distinguish correcting a
  valid invoice from voiding a record sent in error.
- **Tech stack** — deferred to Elaboration (Vision §6 TODO); not a scope decision.
- **Paying-accounts target** — to be set with the product owner once pricing is decided
  (Vision §5 TODO); a business-metric, not a scope item.

---

*Status: agreed (T-005). Scope ratifies Vision §4/§6 and adds three product-owner
boundary decisions (D-1..D-3). Traceability: every in-scope item maps to a
requirement/use case except S-5, which introduces a follow-up requirement (§6).*
