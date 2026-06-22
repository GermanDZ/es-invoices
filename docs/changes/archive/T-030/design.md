# T-030 + T-031 — Design Notes & Completion Verification

## 1a. Spec Verification — T-030

| Req | Grade | Evidence |
|-----|-------|----------|
| `docs/deployment-runbook.md` with `type: work-item, id: DEPLOY-001` | ✅ | File created; frontmatter present in commit 53f414f |
| 8 ordered sections (prereqs → env vars → DB → TLS → first-run → start → smoke test → follow-ups) | ✅ | `docs/deployment-runbook.md` §1–§8 |
| All env vars documented with descriptions | ✅ | §2 env-var table covers `DJANGO_SECRET_KEY`, `CERT_ENCRYPTION_KEY`, `DATABASE_URL`, `EMAIL_*`, `AEAT_SUBMISSION_LIVE`, `ALLOWED_HOSTS` |
| `manage.py check --deploy` step with expected output | ✅ | §5 First-run Checks |
| DB least-privilege SQL included | ✅ | §3a GRANT snippet |
| References RGPD checklist | ✅ | §RGPD Cross-Check section maps each ⚠️ item |
| `check-docs.py` passes | ✅ | 15 instances, 0 failures |

## 1a. Spec Verification — T-031

| Req | Grade | Evidence |
|-----|-------|----------|
| `docs/phase-reviews/construction-ocm.md` with correct frontmatter | ✅ | `type: work-item, id: OCM-001, status: approved` |
| Test evidence: 185-green suite, feature-area breakdown | ✅ | §2a table + 2b coverage table |
| 2 Postgres-gated skips rationale | ✅ | §2a note |
| UC-001..UC-005 conformance table with gap-closures | ✅ | §3 table |
| Risk status R-01..R-08 | ✅ | §4 table |
| Founder GO decision with date and rationale | ✅ | §1 (2026-06-22) |
| Deferred items T-028/T-029 called out | ✅ | §6 table |
| `check-docs.py` passes | ✅ | 15 instances, 0 failures |

## 1b. Success Measures

quick track — n/a

## Notes

T-031 was co-delivered on the T-030 branch since both are doc-only OCM gap closers
with no code changes and overlapping context. The T-031 plan.md is listed in T-030's
`touches`; T-031 will be archived separately after sync-status runs.
