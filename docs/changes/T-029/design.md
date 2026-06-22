# T-029 Design Notes — Self-Service Account + Data Deletion UI

## Completion Verification (step 1a)

Graded against `git diff origin/main...HEAD`.

- ✅ AC1 — "Delete my account" link: `landing.html` adds `<a href="{% url 'accounts:delete_account_confirm' %}">Eliminar mi cuenta</a>`
- ✅ AC2 — Confirmation page explains deletion/retention: `delete_account_confirm.html` sections "¿Qué se eliminará?" and "¿Qué se conservará?" including 5-year fiscal record retention note
- ✅ AC3 — POST marks account for deletion: `DeletionRequest.objects.get_or_create(user=user, defaults={"requested_at": timezone.now()})` + `is_active=False` + `user.save(update_fields=["is_active"])`
- ✅ AC4 — Session terminated on confirm: `logout(request)` called after save; certificate cascade verified by `test_certificate_cascade_on_user_delete` (UserCertificate.owner = OneToOneField(CASCADE))
- ✅ AC5 — `is_active=False` immediately: `user.is_active = False; user.save()` before `logout()`
- ✅ AC6 — T-028 purge handles hard-delete: `DeletionRequest` record persisted with `requested_at`; `purge_expired_data` reads it for 30-day grace (pre-existing, no change needed)
- ✅ AC7 — Confirmation email: `send_mail(subject="Solicitud de eliminación...", recipient_list=[email])` in views.py; `test_post_sends_confirmation_email` asserts `len(mail.outbox) == 1`
- ✅ AC8 — Tests: 13 new tests in `accounts/tests/test_deletion_ui.py`; 220 total, all green (2 postgres-gated skips)
- ✅ AC9 — `check-docs.py` passes: "15 instance(s), no failures"

## Success Measures

n/a — plan has no `## Success Measures` section; uses Acceptance Criteria only.

## Key Decisions

- **DeletionRequest already existed (T-028)**: The model was authored in T-028. The plan's first checkbox "Add deletion_requested_at field" was pre-satisfied; the UI just creates the record.
- **Idempotent POST via `get_or_create`**: Second POST (back-button) does not overwrite the original `requested_at` timestamp. Verified by `test_post_idempotent_second_post_keeps_original_timestamp`.
- **Email failure non-fatal**: `send_mail` failures are caught and logged; the deletion request is already persisted before the email attempt. RGPD erasure is not contingent on email delivery.
- **`delete_account_done` is public**: The view must be reachable without login since `logout()` was called before the redirect. Gating it with `@login_required` would redirect to login in a loop.
- **Certificate cascade is structural (FK)**: The cascade happens via `UserCertificate.owner = OneToOneField(CASCADE)` at hard-delete time (purge_expired_data). The UI does not hard-delete; it only marks the account inactive.
