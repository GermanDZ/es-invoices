# Agent Run Log — T-029

**Task**: T-029 — Self-service account + data deletion UI
**Branch**: feature/T-029-self-service-account-deletion
**Phase**: construction
**Track**: standard
**Start**: 2026-06-22T10:35:39Z
**End**: 2026-06-22T10:46:20Z

## Commits

- `00df9c0` docs(T-029): add design.md with completion verification record [T-029]
- `7870b28` docs(T-029): tick final Operations checkbox [T-029]
- `e17c230` feat(T-029): self-service account deletion UI (RGPD Art. 17)

## Files Changed

- `accounts/views.py` — added `delete_account_confirm` and `delete_account_done` views
- `accounts/urls.py` — wired `/delete/` and `/delete/done/` routes
- `accounts/templates/accounts/delete_account_confirm.html` — new: confirmation page (deletion/retention info)
- `accounts/templates/accounts/delete_account_done.html` — new: public done page
- `accounts/templates/accounts/landing.html` — added "Eliminar mi cuenta" link
- `accounts/tests/test_deletion_ui.py` — new: 13 tests covering full flow
- `docs/changes/T-029/design.md` — new: completion verification record
- `docs/changes/T-029/plan.md` — Operations checkboxes ticked

## Decisions

- DeletionRequest model pre-existed from T-028; no new model/migration needed
- Idempotent POST via `get_or_create` — back-button submits do not reset timestamp
- Email failure is non-fatal (logged, deletion persisted regardless)
- `delete_account_done` view is public (user already logged out on redirect)
- Certificate cascade is structural (UserCertificate.owner = OneToOneField CASCADE at hard-delete time)

## Test Results

220 tests, all green (2 postgres-gated skips). 13 new tests in this task.
`check-docs.py`: 15 instances, no failures.
