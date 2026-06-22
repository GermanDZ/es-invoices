---
id: T-030
title: Deployment operator runbook
status: done
priority: high
estimate: 1 session
plan: docs/roadmap.md#T-030
depends-on: [T-026]
blocks: [T-031]
touches: ["docs/deployment-runbook.md", "docs/phase-reviews/construction-ocm.md", "docs/changes/T-028/plan.md", "docs/changes/T-029/plan.md", "docs/changes/T-031/plan.md"]
last-synced: ""
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

- [x] Write `docs/deployment-runbook.md`
- [x] Run `python3 scripts/check-docs.py` — 0 failures
- [ ] Commit to task branch
