---
type: retrospective
id: RETRO-029
title: Iteration 29 Retrospective — Self-Service Account Deletion UI
phase: construction
date_conducted: 2026-06-22
iterations_covered: 29
---

# Retrospective: Iteration 29 — Self-Service Account Deletion UI (RGPD Art. 17)

**Date conducted:** 2026-06-22  
**Iteration covered:** 29  
**Phase:** Construction  
**Project:** FacturaSimple — compliance-first/Verifactu-native invoicing for Spanish autónomos & pymes  

---

## Iteration Overview

**Goal:** T-029 — Self-service account + data deletion UI (RGPD Art. 17 right-to-erasure)

**Iteration dates:** 2026-06-22 (completion date; actual work window unclear from state, but PR merged and archived 2026-06-22)

**Status:** ✅ Completed

**Team:** Solo developer (GermanDZ) — entire task execution within one session

**Primary task:** T-029  
**Dependency:** T-028 (completed in iteration 28) — automated purge_expired_data command

**Scope delivered:**
- New `delete_account_confirm` view (GET: info page; POST: create DeletionRequest, soft-delete user, terminate session, send confirmation email)
- New `delete_account_done` public landing page (post-logout confirmation)
- Route wiring in `accounts/urls.py` (`/delete/` and `/delete/done/`)
- Landing page updated with "Eliminar mi cuenta" link
- 13 new tests; full suite 220 green (2 postgres-gated skips)

---

## Summary

**Verdict:** Iteration 29 delivered the user-facing half of the RGPD Art. 17 right-to-erasure feature, completing the pairing with T-028's backend purge command. The task was well-scoped, dependency-clean (T-028 pre-existed), and executed efficiently with high test coverage and zero rework.

**Key achievements:**
1. ✅ Self-service deletion UI fully implemented and tested (13 new tests)
2. ✅ Idempotent POST logic (back-button safe; original `requested_at` preserved)
3. ✅ Session termination post-deletion (user logged out immediately)
4. ✅ Non-fatal email handling (send_mail failure logged, deletion persisted)
5. ✅ Acceptance criteria 100% met; zero gaps at completion review

**Overall iteration health:** Excellent — tight scope, clear acceptance criteria, robust test coverage, zero rework needed.

---

## What Went Well

### Process & Execution
1. **Tight dependency chain** — T-028 completed successfully (iteration 28), providing the `DeletionRequest` model and management command. T-029 integrated cleanly on top with zero coordination friction.
2. **Pre-existing model efficiency** — The `DeletionRequest` model was authored in T-028; T-029 did not need to re-author or migrate it. Avoids redundant migration churn.
3. **Clear acceptance criteria** — The plan's 9 AC items were precise and testable. All 9 graded ✅ at completion with zero ambiguity.
4. **Idempotent POST pattern** — Using `DeletionRequest.objects.get_or_create(user=user, defaults={"requested_at": timezone.now()})` ensures a back-button resubmit does not reset the grace-period timestamp. Verified by test `test_post_idempotent_second_post_keeps_original_timestamp`.
5. **High test coverage** — 13 new tests covering: full flow end-to-end, session termination, certificate cascade, email sending, error handling. Validation of both success and edge cases.
6. **Non-fatal email handling** — Email send failures do not block the deletion request; the RGPD erasure right is exercised regardless of email delivery. Correct design for a critical user action.

### Technical Quality
7. **Cascade deletion structure preserved** — User certificates are deleted via structural cascade (`UserCertificate.owner = OneToOneField(CASCADE)`) at hard-delete time by `purge_expired_data`, not by the UI. Keeps the deletion views focused on soft-delete + session termination.
8. **Public landing page pattern** — The `delete_account_done` view correctly does not require `@login_required` (user already logged out). Avoids a login-loop trap.
9. **Integration with existing landing** — The "Eliminar mi cuenta" link integrates into the existing `landing.html` with zero template refactoring; link is minimal and targeted.
10. **Test isolation** — Tests use Django's `override_settings` and mail outbox assertions (`mail.outbox`), isolating from external mail services.

### Documentation & Traceability
11. **Completion verification document** — The `design.md` grades all 9 AC items against the final diff, with evidence (code snippets, test names). Ready for audit.
12. **Check-docs validation** — No frontmatter or traceability errors; `check-docs.py` passes without friction.

---

## What to Improve

### Minor Gaps
1. **Email template missing from diff** — The `send_mail(subject="Solicitud de eliminación...", ...)` call references a hardcoded subject string. No explicit email template file (`accounts/email_templates/deletion_request.txt` or similar) is visible in the diff. **Note:** This is acceptable if the email is intentionally minimal; however, if the email should carry multi-language or rich content, a template would improve maintainability. **Recommendation:** If future iterations require email templates elsewhere, standardize the email pattern.

2. **No explicit operator runbook for `purge_expired_data` scheduling** — The T-028 command is idempotent and safe to run multiple times, but the iteration notes do not specify *how often* an operator should invoke it (daily cron, weekly, on-demand). **Recommendation:** Future Transition phase should include a `deploy-runbook.md` section (or a separate operational guide) specifying the recommended cadence and any monitoring (e.g., alert if purge fails).

3. **Soft-delete UX edge case not tested** — If a user is soft-deleted (is_active=False) but later an admin wants to restore them, the test suite does not cover restoration. **Note:** This is out-of-scope for the self-service deletion feature, but worth flagging if a future admin-restore feature is planned.

### Process Observations
4. **Iteration sequence velocity** — This iteration (T-029) was completed same-day as T-028 (iteration 28), T-026 (RGPD checklist), T-027 (AEAT timeline), T-030/T-031 (OCM docs). All on 2026-06-22. This suggests a rapid build-to-completion cycle post-OCM, with limited inter-iteration breathing room. **Implication:** The project moved from Design → Construction → near-Exit in one sprint. Verify team capacity and review process overhead for the next phase (Transition/Beta).

---

## Measure Read-Back

T-029 is a quick-track architectural/UI task with **`success_measures: n/a`** (no instrumented behavior expectations). The acceptance criteria are all binary (done/not-done) and were met at completion. No read-back metrics apply.

**Note:** Success metrics apply to Construction tasks that alter user-observable behavior or performance. T-029 is a gating feature (users can now delete their account), but its value is legal compliance (RGPD Art. 17), not user activation/engagement. Beta activation metrics (time-to-first-deletion request, deletion request → purge success rate) will be measured post-launch during the Transition/beta phase.

---

## Action Items

| Action | Owner | Due | Priority |
|--------|-------|-----|----------|
| **Email template standardization** — If multi-language or HTML email is needed, create `accounts/email_templates/deletion_request.txt` and refactor `send_mail()` call to use `render_to_string()`. | Developer | next iteration if needed | low |
| **Operator runbook: purge_expired_data cadence** — Specify recommended cron frequency (daily? weekly?) and monitoring in deployment docs (T-030 follow-up). | Operator/DevOps | Transition phase | medium |
| **Soft-delete restoration test** (if admin restore is planned) — Add test covering re-activation of a soft-deleted user (currently out-of-scope, but flag for future). | Architect | backlog | low |
| **Beta instrumentation setup** — Plan deletion-request and purge-success metrics (event logging, dashboards) for Transition phase to validate RGPD feature usage. | Product/Developer | Transition kickoff | medium |

---

## Metrics

### Task Metrics
| Metric | Value |
|--------|-------|
| Tasks planned for iteration | 1 (T-029) |
| Tasks completed | 1 (T-029) |
| Completion rate | 100% |
| Dependencies satisfied | 1/1 (T-028 complete) |

### Code Metrics (T-029 only)
| Metric | Value |
|--------|-------|
| Files changed | 8 |
| Lines added | 457 |
| Lines deleted | 12 |
| New test count | 13 |
| Test suite total | 220 |
| Test pass rate | 100% (2 postgres-gated skips) |
| Check-docs pass | ✅ (15 instances, 0 failures) |

### Timeline
| Event | Date | Duration |
|-------|------|----------|
| Iteration start (inferred from final commit) | 2026-06-22 ~10:35 | — |
| Final commit (design.md + plan archive) | 2026-06-22 10:47 | ~12 min (for final docs/archive) |
| PR merge | 2026-06-22 12:51 | — |
| Status note authored | 2026-06-22 12:51 | — |

**Note:** The times above reflect final archival/merge, not the total implementation window. Actual implementation likely took longer; exact start time is unknown (no `.openup/state.json` persisted).

---

## Next Iteration Considerations

### Carry Forward
- **RGPD Art. 17 complete** — Both self-service and automated deletion are now shipped. Future work on data retention is maintenance/operations (ensuring `purge_expired_data` runs reliably), not new feature work.
- **Account lifecycle is now complete** — Users can register, login, use the product, and delete their account + data. No outstanding account-management gaps.

### Risks to Monitor
- **Operator readiness for purge_expired_data** — Ensure Transition/ops team knows how to run and monitor the purge command. Missing runbook detail could lead to missed purges post-launch.
- **Beta user deletion patterns** — Track how many users exercise the deletion right in beta. If high, may indicate product-market fit issues; if zero, may indicate UX discoverability.

### Process Improvements for Next Iteration
1. **Document iteration start/end times** — Future iterations should timestamp `.openup/state.json` creation and completion to enable velocity trend analysis.
2. **Retro cadence reset** — This iteration triggered a retro-cadence check (T-011). After this retro, run `python3 scripts/openup-state.py retro reset` to reset the counter.
3. **Transition phase preview** — The next major phase (Transition/beta) will focus on deployment, operator docs, and go/no-go readiness. Consider scheduling a phase-review cycle or readiness assessment before launch.

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Iterations in phase | 29 total (1–9 Inception, 10–20 Elaboration, 21–29 Construction) |
| Tasks completed in iteration | 1 (T-029) |
| Tests added | 13 |
| Files changed | 8 |
| Defects found at completion review | 0 |
| Acceptance criteria met | 9/9 (100%) |

---

**Retrospective conducted by:** OpenUP retrospective skill (auto-generated)  
**Review status:** Ready for product-manager and architect review  
**Next step:** Reset retro-cadence counter and plan Transition phase kickoff.
