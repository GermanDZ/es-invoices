---
type: requirement
id: REQ-001
title: Compliant invoice issuance
status: draft
traces-from: [VIS-001]
owner-role: analyst
---

# REQ-001 — Compliant invoice issuance

**Statement:** The system shall let a user create and issue an invoice that
satisfies Spanish legal requirements — mandatory fields (issuer/recipient fiscal
data, date, description, taxable base), correct IVA and IRPF calculation, and
unbroken sequential numbering per issuer series.

**Rationale:** Core value of FacturaSimple (Vision §2). Autónomos must produce
legally valid invoices without fiscal expertise.

**Acceptance criteria (to be verified by test cases in Construction):**
- Invoice totals = taxable base + IVA − IRPF, computed correctly for the
  applicable rates.
- Invoice numbers are sequential and gap-free within a series.
- An invoice missing a mandatory legal field cannot be issued.

**Status note:** draft — refined during Elaboration; test coverage added in Construction.
