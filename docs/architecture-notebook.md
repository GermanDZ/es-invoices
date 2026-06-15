---
type: decision
id: D-01
title: Architecture Notebook — FacturaSimple
status: approved
traces-from: [VIS-001]
owner-role: architect
---

# Architecture Notebook — FacturaSimple

> The architectural baseline for FacturaSimple v1 (Elaboration, T-006). Records
> the load-bearing decisions, the constraints that force them, and the rejected
> alternatives. Each decision is an ADR (`AD-n`). The tech stack (AD-5: Python +
> Django) and datastore (AD-6: PostgreSQL) are now decided with the founder; the
> only remaining open seam is the AD-3 AEAT adapter, resolved by the T-007 spike.

## 1. System Context

FacturaSimple is a **single web application** that lets one Spanish autónomo or
micro-pyma issue, send, correct, and store legally compliant invoices, and
guarantees each is reportable to the AEAT under Verifactu. It is **not** an
accounting/ERP suite (scope.md §1; Vision §2, §8).

- **Primary actor:** the autónomo / micro-pyme owner (single user per account).
- **External systems:** the **AEAT** (Verifactu submission endpoint), an **email
  delivery** provider, and — pending the T-007 build-vs-buy spike — possibly a
  third-party **e-invoice/AEAT gateway**.
- **Account model:** one user, one issuing business (one fiscal identity), one or
  more numbering series (scope.md D-3).

```
        ┌──────────────┐        ┌──────────────────────────────┐
 user → │  Web app     │ ─────► │  AEAT (Verifactu submission)  │
        │ FacturaSimple│        └──────────────────────────────┘
        │              │ ─────► email delivery provider
        │              │ ─────► (optional) AEAT gateway provider [T-007]
        └──────┬───────┘
               ▼
        relational datastore (EU residency)
```

## 2. Architectural Goals & Quality Attributes

Ranked — the order is the tie-breaker when attributes conflict.

| # | Quality attribute | Target / driver | Source |
|---|---|---|---|
| Q-1 | **Compliance correctness** | Every issued invoice is legally valid; no malformed Verifactu record. | R-02; Vision §2 |
| Q-2 | **AEAT submission reliability** | ≥ 99% accepted on first submission. | Vision §5; R-03 |
| Q-3 | **Security & data protection (RGPD)** | EU data residency; encryption in transit + at rest; least privilege. | Vision §6; R-06 |
| Q-4 | **Usability / speed** | Time-to-first-invoice < 5 min (median). | Vision §5 |
| Q-5 | **Maintainability under spec change** | A Verifactu spec change is absorbed in one isolated, versioned module. | R-01 |
| Q-6 | **Lean operability** | One founder can run it; favor managed/build-vs-buy for non-core. | Vision §6; R-07 |

## 3. Architectural Decisions (ADRs)

### AD-1 — Modular monolith (not microservices)
- **Decision:** A single deployable application, internally partitioned into the
  modules in §4.
- **Constraint that forces it:** Solo / bootstrapped team (Vision §6; R-07).
  Microservices' operational overhead is unjustifiable at this scale.
- **Rejected:** Microservices (premature distribution cost); serverless-first
  (cold-start + stateful sequential-numbering complexity).
- **Status:** **accepted.**

### AD-2 — Compliance logic isolated behind a versioned module
- **Decision:** All Verifactu/AEAT rules — record format, hash-chaining/signing,
  IVA/IRPF rule tables, sequential-numbering invariants — live in **one module
  with an explicit version**, behind an interface the rest of the app calls.
- **Constraint that forces it:** R-01 (spec/deadline change is the central
  technical risk) and Q-5. Localizing change is the mitigation already promised
  in the risk list.
- **Rejected:** Compliance logic spread across feature code (a spec change would
  ripple everywhere — exactly the risk R-01 warns against).
- **Status:** **accepted.**

### AD-3 — AEAT submission behind a swappable provider interface
- **Decision:** Submission is reached through an interface with one adapter;
  whether the adapter is **direct integration or a gateway provider is left to
  the T-007 spike**. The interface exists regardless so the adapter can be
  swapped without touching callers.
- **Constraint that forces it:** R-03 (integration is the highest live technical
  exposure; build-vs-buy is not yet decided) and Q-2.
- **Rejected:** Hard-coding a direct AEAT client now (pre-empts the T-007
  decision and couples the app to a fiddly integration).
- **Status:** proposed. **Depends on T-007** for the adapter choice.

### AD-4 — EU data residency on a European cloud provider
- **Decision:** Host the app and datastore on a **European cloud provider**
  (e.g. Hetzner / OVH / Scaleway), all data resident in the EU.
- **Constraint that forces it:** RGPD + EU-residency hard constraint (Vision §6;
  R-06), and Q-6 (cost-sensitive, EU-owned avoids transfer nuance).
- **Rejected:** Hyperscaler EU region (pricier; US-owned → Schrems II transfer
  nuance); managed PaaS (lower ops but less residency control / cost scaling).
  *Decided with the product owner during T-006.*
- **Status:** **accepted.**

### AD-5 — Application tech stack: Python + Django
- **Decision:** Build FacturaSimple in **Python with the Django web framework.**
- **Constraint that forces it:** Q-6 (a solo founder must be productive day one)
  makes founder fluency the dominant selection criterion — founder confirmed
  fluency in Python/Django during T-006.
- **Meets the imposed criteria:** mature **XML + XAdES/XML-DSig signing**
  (`signxml`); reliable **PDF generation** (WeasyPrint / ReportLab); **EU-hostable**
  on any European provider (AD-4); and decisive **founder fluency**.
- **Rejected:** TypeScript+Node, PHP+Laravel, C#+ASP.NET Core — all meet the
  technical criteria, but none beat founder fluency, the dominant criterion at
  solo scale.
- **Status:** **accepted.** *Decided with the founder during T-006.*

### AD-6 — Relational datastore: PostgreSQL
- **Decision:** **PostgreSQL**, EU-hosted (AD-4). Confirmed alongside AD-5 —
  pairs cleanly with Django's first-class `django.db.backends.postgresql` support.
- **Constraint that forces it:** Sequential-numbering invariants and fiscal
  records need ACID transactions and strong consistency (Q-1). Verifactu records
  form an append-only, hash-chained sequence — a transactional relational store
  fits naturally.
- **Rejected:** Document/NoSQL store (weaker transactional guarantees for
  gap-free numbering); MySQL/MariaDB (viable, but PostgreSQL's stronger
  constraint/transaction semantics better fit the numbering invariants).
- **Status:** **accepted.**

## 4. Subsystem Decomposition

| Module | Responsibility | Key quality |
|---|---|---|
| **Account & Auth** | Single user, single business; fiscal identity; series config. | Q-3 |
| **Client management** | Recipient fiscal data (B2B NIF/CIF + B2C). | — (S-1 / UC-003) |
| **Invoicing core** | Line items, taxable base, IVA + IRPF calc, gap-free sequential numbering per series; corrective/cancellation invoices (S-5). | Q-1 |
| **Compliance / Verifactu module** *(AD-2)* | Versioned: legal-field validation, Verifactu record generation, hash-chain + XAdES signing, annulment records. | Q-1, Q-5 |
| **AEAT submission gateway** *(AD-3)* | Interface + swappable adapter; submit, capture accepted/rejected outcome, retry. | Q-2 |
| **Document & delivery** | PDF generation; send-by-email via provider. | Q-4 |
| **Persistence** *(AD-6)* | Relational store, EU-resident; transactional boundary for numbering + records. | Q-1, Q-3 |

Dependency rule: feature modules depend on the **Compliance module** and the
**Submission gateway** only through their interfaces (AD-2, AD-3) — never on their
internals.

## 5. Constraints (carried)

- **Spain-only legal model** — Spanish UI, EUR, AEAT (Vision §6; non-goal N-6).
- **EU data residency / RGPD** — AD-4, Q-3.
- **Solo / bootstrapped team** — lean; build-vs-buy for non-core (Vision §6; R-07).
- **Tech stack: Python + Django, PostgreSQL** — AD-5, AD-6 (founder-decided).

## 6. Self-Critique

- **Weakest point:** one seam remains open — the AEAT integration adapter (AD-3),
  build-vs-buy. This is honest, not hidden: the **interface** is committed now so
  the adapter can be swapped, and the decision is contained behind it until the
  **T-007** spike resolves it. The stack (AD-5) and datastore (AD-6) are now
  founder-decided, so the notebook is `approved`.
- **Load-bearing assumption:** a relational store + modular monolith will scale
  to the v1 user base. For a single-user-per-account invoicing tool at
  bootstrap scale this is safe; revisit only if multi-tenant load profiles
  change (out of v1 scope, N-5).
- **Resolution:** AD-1/AD-2/AD-4/AD-5/AD-6 are accepted; the one open item (AD-3
  adapter) has an explicit resolution path (T-007).

## 7. Open Decisions / Follow-ups

- **AD-5 (tech stack)** — RESOLVED: Python + Django (founder-decided T-006;
  see `docs/input-requests/archive/2026-06-15-tech-stack-decision.md`).
- **AD-6 (datastore)** — RESOLVED: PostgreSQL (founder-confirmed T-006).
- **AD-3 adapter (build-vs-buy)** — open; resolved by **T-007** (AEAT submission
  spike). The only remaining open seam.

---

*Authored in Elaboration (T-006) via `/openup-create-architecture-notebook`.
Traces from VIS-001. Status `approved` — AD-5 (Python + Django) and AD-6
(PostgreSQL) founder-decided; the AD-3 AEAT adapter remains open pending the
T-007 spike.*
