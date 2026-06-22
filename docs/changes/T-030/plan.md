---
type: work-item
id: T-030
title: Deployment operator runbook
status: in-progress
phase: construction
track: quick
touches: [docs/deployment-runbook.md]
depends-on: [T-026]
traces-from: [RGPD-001]
---

# T-030 — Deployment Operator Runbook

**Goal**: Close OCM gap #1 — "user documentation is adequate."  
Write `docs/deployment-runbook.md` as a standalone, ordered operator runbook.

## Context

The RGPD checklist (T-026) §6 lists the pre-launch operator steps inline, but they are
embedded in the compliance doc and not discoverable as a deployment guide. The OCM requires
adequate documentation before handing the product to a beta operator.

## Acceptance Criteria

- [ ] `docs/deployment-runbook.md` exists with frontmatter (type: work-item, id: DEPLOY-001)
- [ ] Ordered step-by-step sections: Prerequisites → Environment variables → Database setup → TLS + reverse proxy → First-run checks → Smoke-test
- [ ] All env vars listed with descriptions (SECRET_KEY, CERT_ENCRYPTION_KEY, DATABASE_URL, EMAIL_*, AEAT_SUBMISSION_LIVE)
- [ ] `manage.py check --deploy` step with expected "0 critical warnings" output
- [ ] DB least-privilege grant SQL included
- [ ] References RGPD checklist for compliance cross-check
- [ ] `python3 scripts/check-docs.py` passes

## Operations Checklist

- [ ] Write `docs/deployment-runbook.md`
- [ ] Run `python3 scripts/check-docs.py` — 0 failures
- [ ] Commit to task branch
