---
type: use-case
id: UC-002
title: Submit invoice to AEAT (Verifactu)
status: approved
traces-from: [REQ-002]
owner-role: analyst
---

# UC-002 — Submit invoice to AEAT (Verifactu)

**Primary actor:** Autónomo (self-employed user)
**Secondary actors:** AEAT (tax authority system)
**Description:** When an invoice is issued, the system generates the
Verifactu-compliant record and submits it to the AEAT, recording the outcome.

**Preconditions:**
- An invoice has been issued (UC-001).
- The user's AEAT submission credentials/certificate are configured.

**Postconditions (success):**
- A Verifactu record for the invoice has been submitted.
- The submission outcome (accepted / rejected + reason) is stored against the invoice.

**Basic flow:**
1. On invoice issuance, the system generates the Verifactu-required record.
2. The system submits the record to the AEAT.
3. The AEAT returns an acceptance response.
4. The system stores the acceptance and marks the invoice as reported.

**Alternative flows:**
- **3a. AEAT rejects the record:** the system stores the rejection reason, marks
  the invoice as not-reported, and surfaces the reason to the user for correction.
- **2a. Submission transport fails:** the system retries per policy and, if still
  failing, queues the record and notifies the user it is pending.

**Self-critique:** Weakest point — depends on the AEAT integration approach
(build vs gateway), unresolved until the risk R-03 spike; the flow is written
against the interface, not a specific provider, so it survives that decision.
