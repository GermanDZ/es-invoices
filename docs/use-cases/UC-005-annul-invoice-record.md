---
type: use-case
id: UC-005
title: Annul an invoice record (Verifactu anulación)
status: approved
traces-from: [REQ-004]
owner-role: analyst
---

# UC-005 — Annul an invoice record (Verifactu anulación)

**Primary actor:** Autónomo (self-employed user)
**Secondary actors:** AEAT (tax authority system)
**Goal:** Void a Verifactu record that should never have existed and have the
annulment reported to the AEAT.

**Description:** When an invoice was raised *in error* — a duplicate, a record
against the wrong account, or a test/erroneous submission — the user annuls it.
The system generates a Verifactu *registro de anulación* that voids the
previously-sent record and submits it (UC-002 path). The annulment is reserved
for erroneous records; correcting a real sale is done with a rectificativa
(UC-004).

**Trigger:** The user opens an issued (Verifactu-reported) invoice and chooses
"Annul (issued in error)".

**Preconditions:**
- The invoice has a Verifactu record that was submitted (or queued for
  submission).
- The record was sent in error — it does not document a real, valid sale (the
  system steers genuine corrections to UC-004).
- The user's AEAT credentials/certificate are configured (as for UC-002).

**Postconditions (success):**
- A Verifactu *registro de anulación* referencing the original record has been
  generated and submitted; its accepted/rejected outcome is stored (REQ-002).
- The original invoice is marked **annulled** and excluded from the active set,
  while remaining on record (the annulment is chained, not a deletion).

**Basic flow:**
1. The user opens a reported invoice and selects "Annul (issued in error)".
2. The system warns that annulment is only for records sent in error and asks the
   user to confirm the reason.
3. The user confirms the annulment reason.
4. The system generates the Verifactu *registro de anulación* referencing the
   original record.
5. The system submits the annulment record to the AEAT (UC-002).
6. The AEAT returns acceptance; the system stores it and marks the invoice
   annulled.

**Alternative flows:**
- **2a. Record not yet submitted:** the original Verifactu record is still queued
  (UC-002 2a) and not yet accepted by the AEAT; the system cancels the pending
  submission instead of sending an annulment record, and marks the invoice
  annulled locally.

**Exception flows:**
- **2b. Invoice documents a real sale:** the system declines to annul and
  redirects the user to issue a factura rectificativa (UC-004) instead.
- **5a. AEAT rejects the annulment record:** the system stores the rejection
  reason, leaves the invoice in its prior (reported) state, and surfaces the
  reason for the user to act on.
- **5b. Submission transport fails:** the system retries per policy and, if still
  failing, queues the annulment record and notifies the user it is pending (as
  UC-002 2a).

**Scope & boundaries:** Covers voiding an erroneously-submitted Verifactu record
for común-territory invoices only. Out of scope: correcting/reversing a valid
sale (UC-004), TicketBAI/foral territories (N-6), and UI layout. Annulment never
removes a record from the Verifactu chain — it marks it annulled.

**Self-critique:** Weakest point — distinguishing "sent in error" from "needs a
rectificativa" depends on user judgement; mitigated with the step-2 warning and
the UC-004 redirect, but the exact guardrails (e.g. time/threshold limits on
annulment) need Construction test design with the product owner. Flows and
pre/postconditions are externally observable and checkable.
