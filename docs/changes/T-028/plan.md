---
id: T-028
title: Automated data retention enforcement (scheduled deletion)
status: ready
priority: medium
estimate: 2 sessions
plan: docs/roadmap.md#T-028
depends-on: [T-030]
blocks: [T-029]
touches: ["accounts/", "invoicing/", "clients/", "submission/"]
last-synced: ""
---

# T-028 — Automated Data Retention Enforcement

**Goal**: Implement a scheduled management command that enforces the retention policy
from `docs/rgpd-checklist.md §5` (RGPD Art. 17 automated-deletion follow-up).

## Context

The RGPD checklist deferred automated deletion to a post-launch task. Before broad beta,
the system needs a reliable way to purge expired data:
- Invoice records and client personal data older than 5 years
- User accounts 30 days after account deletion request

## Acceptance Criteria

- [ ] `purge_expired_data` management command in the `accounts` app
- [ ] Deletes invoices/line items issued > 5 years ago (configurable)
- [ ] Deletes client records when their last associated invoice is > 5 years ago
- [ ] Handles accounts in soft-delete / deletion-requested state > 30 days
- [ ] Dry-run mode (`--dry-run`) logs what would be deleted without mutating
- [ ] Command is idempotent (safe to run multiple times)
- [ ] Tests cover: dry-run, actual deletion, retention boundary (5yr - 1 day = kept)
- [ ] `python3 scripts/check-docs.py` passes

## Operations Checklist

- [x] Author `purge_expired_data` management command
- [x] Add `DeletionRequest` model or flag to `accounts.User` (soft-delete)
- [x] Write tests
- [x] Run full suite — all green
- [x] Commit to task branch
