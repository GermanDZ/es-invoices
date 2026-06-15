---
type: use-case
id: UC-001
title: Issue a compliant invoice
status: approved
traces-from: [REQ-001]
owner-role: analyst
---

# UC-001 — Issue a compliant invoice

**Primary actor:** Autónomo (self-employed user)
**Secondary actors:** —
**Description:** The user creates an invoice for a client and issues it, the
system producing a legally valid Spanish invoice.

**Preconditions:**
- The user is authenticated.
- At least one client exists (see UC-003) or is entered inline.

**Postconditions (success):**
- A valid invoice is persisted with the next sequential number in its series.
- The invoice is available as a PDF.

**Basic flow:**
1. The user starts a new invoice and selects a client.
2. The user adds one or more line items (description, quantity, unit price).
3. The system computes the taxable base, applies the applicable IVA, and applies
   IRPF retention if configured.
4. The system assigns the next sequential invoice number in the series.
5. The user reviews the totals and confirms issuance.
6. The system validates all mandatory legal fields are present and persists the
   invoice, then makes the PDF available.

**Alternative flows:**
- **3a. IRPF not applicable:** the user marks the invoice as not subject to
  IRPF; the system omits the retention.
- **6a. Missing mandatory field:** the system blocks issuance and indicates the
  missing field; the invoice number is not consumed.
- **2a. No line items:** the system prevents confirmation until at least one
  valid line item exists.

**Self-critique:** Weakest point — the invoice-number series model (per-year vs
per-client vs single) is assumed single-series here; flagged for Elaboration. All
flow steps are observable and pre/postconditions are checkable.
