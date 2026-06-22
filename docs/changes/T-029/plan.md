---
type: work-item
id: T-029
title: Self-service account + data deletion UI
status: pending
phase: construction
track: standard
touches: [accounts/]
depends-on: [T-028]
traces-from: [RGPD-001]
---

# T-029 — Self-Service Account + Data Deletion UI

**Goal**: Add a "Delete my account" flow in the `accounts` app satisfying RGPD Art. 17
right-to-erasure for non-fiscal personal data.

## Context

RGPD checklist §5 deferred self-service deletion to T-029. The `purge_expired_data`
command (T-028) handles the automated backend; this task adds the user-facing UI.

## Acceptance Criteria

- [ ] "Delete my account" link in account settings page
- [ ] Step 1: confirmation page explains what will be deleted and what will be retained (fiscal records under legal obligation)
- [ ] Step 2: final confirm POST marks account for deletion (soft-delete + `deletion_requested_at` timestamp)
- [ ] On confirm: user session terminated, certificates cascade-deleted (T-011 `on_delete=CASCADE`)
- [ ] Account marked `is_active=False` immediately (blocks login)
- [ ] T-028 `purge_expired_data` will handle hard-delete after 30-day grace
- [ ] Confirmation email sent to user on deletion request
- [ ] Tests: flow end-to-end, session terminated, certificate cascade, email sent
- [ ] `python3 scripts/check-docs.py` passes

## Operations Checklist

- [ ] Add `deletion_requested_at` field to `accounts.User` (or via T-028 model)
- [ ] Add account settings / deletion views + templates
- [ ] Wire routes in `accounts/urls.py`
- [ ] Write tests
- [ ] Run full suite — all green
- [ ] Commit to task branch
