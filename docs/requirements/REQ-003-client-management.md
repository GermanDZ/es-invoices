---
type: requirement
id: REQ-003
title: Client management
status: draft
traces-from: [VIS-001]
owner-role: analyst
---

# REQ-003 — Client management

**Statement:** The system shall let a user create, edit, and reuse client
records (fiscal name, NIF/CIF, address) so that clients can be selected when
issuing an invoice.

**Rationale:** In-scope v1 capability (Vision §4); reduces time-to-first-invoice
(north-star metric) by removing repetitive data entry.

**Acceptance criteria (to be verified by test cases in Construction):**
- A client can be created with the fiscal fields required for a valid invoice.
- A saved client can be selected when issuing an invoice, pre-filling recipient data.
- A client with an invalid/missing NIF cannot be used to issue an invoice.

**Status note:** draft — refined during Elaboration.
