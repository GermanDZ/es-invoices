---
type: use-case
id: UC-003
title: Manage a client
status: approved
traces-from: [REQ-003]
owner-role: analyst
---

# UC-003 — Manage a client

**Primary actor:** Autónomo (self-employed user)
**Secondary actors:** —
**Description:** The user creates or edits a client record so it can be reused
when issuing invoices.

**Preconditions:**
- The user is authenticated.

**Postconditions (success):**
- A client record with valid fiscal fields is persisted and available for selection.

**Basic flow:**
1. The user opens the client list and chooses to add a client.
2. The user enters the client's fiscal name, NIF/CIF, and address.
3. The system validates the NIF/CIF format.
4. The system persists the client.

**Alternative flows:**
- **3a. Invalid NIF/CIF:** the system rejects the entry and indicates the format
  problem; the client is not saved.
- **1a. Edit existing client:** the user selects an existing client and updates
  its fields; the system re-validates and persists.

**Self-critique:** Weakest point — NIF/CIF validation depth (checksum vs format
only) is left to Elaboration; the use case asserts validation occurs without
fixing its strictness. Flow steps are observable; pre/postconditions checkable.
