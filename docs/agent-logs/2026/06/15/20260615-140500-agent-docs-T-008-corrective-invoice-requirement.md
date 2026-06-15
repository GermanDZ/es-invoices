---
run_id: T-008-iter7
task_id: T-008
event: task_complete
branch: docs/T-008-corrective-invoice-requirement
phase: elaboration
track: quick
role: analyst
started: 2026-06-15T14:00:00Z
ended: 2026-06-15T14:05:00Z
---

# Agent Run — T-008 Corrective-invoice requirement + use cases

**Task:** Add + detail corrective-invoice requirement (facturas rectificativas,
S-5/D-1); detail UC for corrective issuance and Verifactu annulment.

**Files changed:**
- `docs/requirements/REQ-004-corrective-and-cancellation-invoices.md` (new)
- `docs/use-cases/UC-004-issue-corrective-invoice.md` (new)
- `docs/use-cases/UC-005-annul-invoice-record.md` (new)
- `docs/scope.md` (S-5 traceability filled; §6 open item closed)

**Decisions:**
- Modeled corrective vs cancellation as TWO distinct legal mechanisms:
  factura rectificativa (correct/reverse a *valid* invoice, new doc + Verifactu
  alta record R1–R5) vs Verifactu anulación (void a record sent *in error*).
  The scope/arch docs had conflated them; the requirement now separates them.
- One REQ (REQ-004) detailed by two use cases (UC-004 corrective, UC-005
  annulment), each satisfying all 8 use-case-rubric criteria.
- v1 común-territory only (no TicketBAI / foral); ratified at T-007 Q4 (N-6).
- Rectificativa uses a dedicated numbering series; default method *por
  sustitución*, *por diferencias* as an alternate flow — flagged for Construction.

**Trace:** REQ-004 ← VIS-001; UC-004/UC-005 ← REQ-004; scope S-5 → REQ-004/UC-004/UC-005 (D-1).
