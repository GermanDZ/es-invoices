---
type: requirement
id: REQ-002
title: Verifactu / AEAT record submission
status: draft
traces-from: [VIS-001]
owner-role: analyst
---

# REQ-002 — Verifactu / AEAT record submission

**Statement:** The system shall generate a Verifactu-compliant record for each
issued invoice and submit it to the AEAT, recording the submission outcome.

**Rationale:** Compliance-first / Verifactu-native positioning (Vision §2, §8);
addresses the regulatory burden that is the project's reason for existing.

**Acceptance criteria (to be verified by test cases in Construction):**
- Each issued invoice produces a record in the Verifactu-required format.
- The record is submitted to the AEAT and the response (accepted/rejected) is stored.
- A rejected submission is surfaced to the user with a reason.

**Status note:** draft — depends on AEAT integration spike (risk R-03); refined in Elaboration.
