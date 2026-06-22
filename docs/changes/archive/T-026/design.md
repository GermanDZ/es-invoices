# T-026 Design Notes — RGPD Pre-Launch Checklist

## Requirement Verification (step 1a)

| Req | Status | Evidence |
|-----|--------|----------|
| 1 — Checklist document exists with 5 sections | ✅ | `docs/rgpd-checklist.md` created; §1–§5 cover all five R-06 mitigation areas in table format |
| 2 — EU data residency section | ✅ | §1 covers app server, DB, email sub-processor, no US-only SaaS, no cross-border transfer; AD-4 referenced |
| 3 — Encryption in transit (4 SECURE_* settings) | ✅ | `config/settings.py` diff: all four settings under `if not DEBUG:`; `manage.py check --deploy` → 0 critical warnings (5 advisory Ws for test-env conditions) |
| 4 — Encryption at rest (3 layers) | ✅ | §3 confirms T-011 AES-256-GCM for certs (✅), block-storage encryption (⚠️ operator confirm), DB SSL (⚠️ operator) |
| 5 — Least-privilege access documented | ✅ | §4 records expected DB privilege scope, email send-only scope; deviations flagged ⚠️ with mitigation note |
| 6 — Retention policy statement | ✅ | §5 table: 5 data categories, retention periods (5yr invoice/fiscal, 5yr client, 30-day post-deletion account), deletion approach, legal basis (Ley 58/2003, Ley 37/1992) |
| 7 — No ❌ items; all ⚠️ have follow-up | ✅ | Summary §6 shows all areas ✅ or ⚠️; every ⚠️ has operator runbook step or named task (T-028, T-029) |

## Success Measure Verification (step 1b)

- `docs/rgpd-checklist.md` exists with all five sections: ✅ verified by file existence
- `config/settings.py` diff shows four `SECURE_*` settings under `if not DEBUG:`: ✅ verified by git diff
- `manage.py check --deploy` exits with 0 critical warnings: ✅ run 2026-06-22, result: 5 advisory warnings (W002 XFrameOptions, W005 HSTS subdomains, W009 short test key, W020 empty ALLOWED_HOSTS, W021 HSTS preload) — none critical; all expected for a test-key invocation
- `docs/risk-list.md §R-06` references the checklist: ✅ verified by git diff
- **Read-back date**: 30 days post-v1 launch (automated deletion T-028, self-service deletion T-029 as follow-ups)
- **Success measure instrumentation**: manual review at deploy time (operator runbook step 5); no automated metric required for a documentation/config task

## Key Decisions

- **⚠️ vs ❌ policy**: All operator-side controls (EU hosting confirmation, DB SSL, least-privilege DB user, TLS termination) are ⚠️ because they cannot be code-enforced — they require deploy-time configuration. This is the appropriate status (not ❌) because they have concrete follow-up actions in the operator runbook.
- **`manage.py check --deploy` advisory warnings**: W005 (HSTS subdomains), W021 (HSTS preload) not treated as blocking — they are hardening options beyond the R-06 mitigation scope, not critical security gaps.
- **Retention policy legal basis**: Spanish Ley 58/2003 + Ley 37/1992 IVA for 5-year invoice retention cited; note that some obligations may extend to 10 years — operator must confirm with a tax advisor.
- **DB SSL not wired in code**: Added as ⚠️ operator responsibility rather than a code change; the spec's scope is "audit + one settings fix" and DB SSL option wiring is a separate small task (could be T-027 or operator runbook).
- **Follow-up tasks named**: T-028 (automated deletion), T-029 (self-service deletion UI) — referenced in checklist but not created in roadmap (post-launch, not launch-blocking).
