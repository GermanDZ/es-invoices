---
type: requirement
id: REQ-004
title: Corrective and cancellation invoices (facturas rectificativas + Verifactu annulment)
status: draft
traces-from: [VIS-001]
owner-role: analyst
---

# REQ-004 — Corrective and cancellation invoices

**Statement:** The system shall let the user legally amend or void an
already-issued invoice through the two mechanisms Spanish law and Verifactu
provide, and shall generate the matching Verifactu record for each:

1. **Factura rectificativa** — for an invoice that was *validly issued* but is
   now wrong or must be reversed (wrong amount, price/quantity error, return,
   discount, or full credit). The system issues a new corrective invoice that
   references the original and carries the adjustment, and submits it as a
   Verifactu *alta* record of a rectificativa type.
2. **Anulación (annulment)** — for a Verifactu record that *should never have
   existed* (duplicate, invoice raised against the wrong account, test/erroneous
   submission). The system submits a Verifactu *registro de anulación* that voids
   the previously-sent record.

**Rationale:** A compliance-first product that cannot legally fix or void a
mistaken invoice breaks its own promise (scope **D-1 / S-5**). Both mechanisms
are part of *staying* compliant under Verifactu, not optional extras — Verifactu
explicitly defines a rectificativa record type and a distinct annulment record
(architecture notebook, Compliance/Verifactu module). Addresses risk **R-03**.

**Domain rules (Spain — común territory, Verifactu):**
- A **factura rectificativa** never deletes the original invoice; the original
  remains on record and the rectificativa documents the change. Cancelling the
  economic effect of a *real* sale is therefore done with a rectificativa
  (e.g. *por sustitución* reducing the total to zero), **not** with an annulment.
- A rectificativa must **reference the original invoice(s)** it corrects and must
  use a **dedicated numbering series** distinct from ordinary invoices, with the
  same gap-free sequential guarantee per series (consistent with S-2).
- A rectificativa may be issued **por sustitución** (the corrective restates the
  full corrected invoice) or **por diferencias** (it carries only the delta). v1
  shall support at least one method end-to-end; the chosen default is detailed in
  UC-004.
- An **anulación** is reserved for records sent in error and likewise produces a
  chained Verifactu record (it marks the original record annulled; it does not
  remove it from the chain).
- Both corrective and annulment records are subject to the same
  hash-chain + signing + AEAT-submission path as ordinary records (REQ-002):
  generation, submission, and accepted/rejected outcome storage all apply.

**Acceptance criteria (to be verified by test cases in Construction):**
- From an issued invoice, the user can create a **factura rectificativa** that
  references the original, is numbered in a dedicated rectificativa series, and
  carries the corrected amounts.
- Issuing a rectificativa produces and submits a Verifactu *alta* record of a
  rectificativa type, and the submission outcome (accepted/rejected + reason) is
  stored against it (per REQ-002).
- From a Verifactu record submitted in error, the user can issue a Verifactu
  **anulación** that voids that record; the outcome is stored and the original
  invoice is marked annulled.
- The system prevents the user from annulling a record that was *correctly*
  issued against a real sale, steering them to a rectificativa instead.
- A rejected corrective/annulment submission is surfaced to the user with a
  reason and does not consume an invoice number in a way that breaks the series.

**Status note:** draft — newly added in Elaboration (T-008) to close the S-5/D-1
gap left open at T-005. v1 is común-territory (Verifactu) only; TicketBAI /
territorios forales are out of scope (N-6, ratified at T-007 Q4). Detailed by
UC-004 (corrective issuance) and UC-005 (annulment).
