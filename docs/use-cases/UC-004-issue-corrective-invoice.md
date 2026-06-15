---
type: use-case
id: UC-004
title: Issue a corrective invoice (factura rectificativa)
status: draft
traces-from: [REQ-004]
owner-role: analyst
---

# UC-004 — Issue a corrective invoice (factura rectificativa)

**Primary actor:** Autónomo (self-employed user)
**Secondary actors:** AEAT (tax authority system)
**Goal:** Legally correct or reverse a validly-issued invoice and have the
correction reported to the AEAT.

**Description:** Starting from an already-issued invoice, the user issues a
*factura rectificativa* that references the original and carries the adjustment
(corrected amounts, a return, a discount, or a full credit). The system numbers
it in the dedicated rectificativa series, generates its Verifactu *alta* record
of a rectificativa type, and submits it (UC-002 path).

**Trigger:** The user opens an issued invoice and chooses "Issue corrective
invoice" (rectificar).

**Preconditions:**
- The invoice to correct has been issued (UC-001) and is *validly* issued — i.e.
  it documents a real sale (use UC-005 instead if the record was sent in error).
- A rectificativa numbering series exists for the business (or the system creates
  the default one on first use).
- The user's AEAT credentials/certificate are configured (as for UC-002).

**Postconditions (success):**
- A factura rectificativa is persisted, numbered next-in-sequence in its
  rectificativa series, and references the original invoice.
- The corrective is available as a PDF, clearly marked as *rectificativa* and
  citing the corrected invoice.
- A Verifactu *alta* record of a rectificativa type has been generated and
  submitted; its accepted/rejected outcome is stored (REQ-002).
- The original invoice is linked to its rectificativa and its status reflects
  that it has been corrected.

**Basic flow:**
1. The user opens an issued invoice and selects "Issue corrective invoice".
2. The user chooses the reason/type of correction (e.g. error in amount, return,
   discount, full credit).
3. The system creates a rectificativa pre-filled from the original, *por
   sustitución* by default (the corrective restates the full corrected invoice).
4. The user edits the corrected line items / amounts.
5. The system recomputes the taxable base, IVA and any IRPF on the corrected
   figures and shows the net difference against the original.
6. The system assigns the next number in the rectificativa series and records the
   reference to the original invoice.
7. The user reviews and confirms issuance.
8. The system validates the mandatory legal fields (including the original
   reference and rectificativa type), persists the corrective, and makes its PDF
   available.
9. The system generates the Verifactu rectificativa-type record and submits it to
   the AEAT (UC-002), then stores the acceptance and marks the original as
   corrected.

**Alternative flows:**
- **3a. Por diferencias:** the user chooses the *por diferencias* method; the
  corrective carries only the delta (e.g. a negative line) rather than restating
  the whole invoice. The Verifactu record reflects the difference amounts.
- **2a. Full cancellation of a real sale:** the user reverses the entire invoice;
  the system produces a rectificativa reducing the corrected total to zero (the
  original stays on record). This is the legal way to "cancel" a valid invoice —
  distinct from an annulment (UC-005).

**Exception flows:**
- **8a. Missing mandatory field:** the system blocks issuance and indicates the
  missing field (e.g. no original reference, no rectificativa type); the
  rectificativa series number is not consumed.
- **9a. AEAT rejects the rectificativa record:** the system stores the rejection
  reason, marks the corrective as not-reported, and surfaces the reason for the
  user to fix and resubmit; the original invoice's corrected status is not applied
  until a record is accepted.
- **9b. Submission transport fails:** the system retries per policy and, if still
  failing, queues the record and notifies the user it is pending (as UC-002 2a).

**Scope & boundaries:** Covers issuing the corrective document and reporting it
via Verifactu for común-territory invoices only. Out of scope: voiding a record
sent in error (UC-005), TicketBAI/foral territories (N-6), and the internal UI
layout. The series model reuses the gap-free sequential guarantee of S-2.

**Self-critique:** Weakest point — whether v1 defaults to *por sustitución* or
*por diferencias* and which Verifactu rectificativa subtypes (R1–R5) are exposed
to a zero-accounting-knowledge user; defaulted to *por sustitución* here and
flagged for Construction test design with the product owner. Each flow step is
externally observable and the pre/postconditions are checkable.
