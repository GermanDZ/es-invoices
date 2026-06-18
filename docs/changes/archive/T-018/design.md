# T-018 — Design / in-flight decisions

## Decisions

- **DD1.** "sent" persisted as a nullable `sent_at` `DateTimeField` on `Invoice`,
  not a status-enum column. The human-readable `status` is a derived read-only
  property over `issued` + `sent_at` — one fact, no drift. Mirrors how T-017's
  `corrected_by`/`annulled` are post-issuance overlays (absent from
  `_IMMUTABLE_WHEN_ISSUED`).
- **DD2.** The stamp is written in `documents.services.send_invoice_email` via a
  small `Invoice.mark_sent(when=None)` helper, only on a confirmed non-zero send
  (`if sent:`). `mark_sent` uses `save(update_fields=["sent_at"])` so it cannot
  trip the issued-identity guard or clobber concurrent writes.
- **DD3.** AEAT submission outcome stays in `submission.SubmissionAttempt`
  (T-014); deliberately NOT folded into invoice `status` — S-6 is only
  issued/sent.

## Verification — Requirements vs diff (step 1a, BLOCKING)

Graded against `git diff origin/main...HEAD`; every scenario's **Then** confirmed
by a passing test (full suite 123 green, 2 Postgres-gated skips).

- ✅ **R1** nullable `sent_at` default None — `invoicing/models.py` field
  `sent_at = DateTimeField(null=True, blank=True)`; migration
  `0004_invoice_sent_at.py`. Checked by `test_draft_invoice_reports_draft`
  (`sent_at is None`).
- ✅ **R2** derived `status` draft/issued/sent — `Invoice.status` property.
  Checked by `StatusPropertyTests` (3 cases).
- ✅ **R3** successful send stamps `sent_at` — `mark_sent()` call in
  `send_invoice_email` under `if sent:`. Checked by
  `test_successful_send_marks_invoice_sent` (`status == "sent"`).
- ✅ **R4** zero/failed send does not stamp — guarded by `if sent:`. Checked by
  `test_zero_send_leaves_invoice_unsent` (`sent_at is None` after a mocked
  `send()==0`).
- ✅ **R5** stamping does not trip immutability guard — `sent_at` not in
  `_IMMUTABLE_WHEN_ISSUED`; `mark_sent` uses `update_fields`. Checked by
  `test_mark_sent_does_not_trip_immutability_guard`.
- ✅ **R6** re-send advances `sent_at` — `mark_sent(when=)` overwrites. Checked
  by `test_resend_advances_sent_at_to_later_time`.

**Result: all ✅ — no unmet requirement.**

## Verification — Success-Measure instrumentation (step 1b)

`## Success Measures` is `n/a — internal lifecycle field, no user-facing surface
or telemetry in T-018` (argued in spec). No instrumentation owed this task;
read-back deferred to the future invoice-list/status-filter view. Recorded n/a.
