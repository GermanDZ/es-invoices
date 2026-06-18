# Agent Log: T-018 — Basic Invoice Status Tracking

- **Task**: T-018 — Basic invoice status tracking (issued / sent)
- **Branch**: feat/T-018-invoice-status-tracking
- **Phase**: construction
- **Iteration**: 17
- **Track**: standard
- **Start**: 2026-06-18T12:38:41Z
- **End**: 2026-06-18T12:43:30Z

## Commits

- `1a5eef4` — feat(T-018): basic invoice status tracking (issued / sent) [T-018]

## Files Changed

- `invoicing/models.py` — sent_at field + status property + mark_sent
- `invoicing/migrations/0004_invoice_sent_at.py` — new
- `documents/services.py` — stamp sent_at on confirmed send
- `invoicing/tests/test_status.py` — new, 5 tests
- `documents/tests/test_email.py` — +2 tests
- `docs/changes/T-018/plan.md` — spec
- `docs/changes/T-018/design.md` — decisions + verification grade

## Decisions

- sent_at persisted as a nullable timestamp
- status is a derived read-only property (draft/issued/sent)
- mark_sent uses save(update_fields=['sent_at']) to stay clear of the issued-immutability guard
- AEAT submission outcome stays in SubmissionAttempt (T-014), not folded into status

## Outcome

All 6 requirements graded ✅ against the diff; full test suite 123 green (2 Postgres-gated skips); migration drift check clean.
