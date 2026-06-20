# T-025 — Test Notes

**Run:** `python manage.py test` (via project `.venv`, Django test runner)
**Result:** `Ran 185 tests … OK (skipped=2)` — all green; the 2 skips are the
existing Postgres-gated concurrency tests (SQLite test DB). No missing migrations
(`makemigrations --check --dry-run` → "No changes detected").

## Requirement → evidence

| Req | Behaviour | Test(s) |
|---|---|---|
| **R1** | *Por diferencias* reachable; método threads form→service→`generate_alta` | `invoicing.tests.test_corrective.RectificativaIssuanceTests.test_method_por_diferencias_sets_tipo_rectificativa_I_no_importe` (record `TipoRectificativa="I"`, no `ImporteRectificacion`), `…test_default_method_is_sustitucion_S` (default `"S"`, keeps `ImporteRectificacion`), `invoicing.tests.test_rectificativa_view.RectificativaViewTests.test_post_por_diferencias_threads_method_to_record` (UI exposes método; "I" reaches the record) |
| **R2** | Rectificativa PDF marked + cites corrected NumSerie | `documents.tests.test_pdf.RectificativaMarkingTests.test_rectificativa_pdf_is_marked_and_cites_corrected_numserie`, `…test_ordinary_invoice_has_no_rectificativa_marking` |
| **R3** | Annul-while-pending cancels submission, no anulación | `invoicing.tests.test_corrective.AnnulmentTests.test_annul_while_pending_cancels_attempt_and_sends_no_anulacion`, `…test_annul_when_accepted_generates_anulacion` (accepted branch unchanged) |
| **R4** | Annulled invoices excluded from active set; record still reachable | `invoicing.tests.test_corrective.ActiveSetTests.test_active_excludes_annulled_invoices`, `invoicing.tests.test_annul_view.AnnulViewTests.test_annulled_invoice_detail_still_loads` |
| **R5** | `Client.email` optional + validated; resolved when `to_email` omitted | `clients.tests.test_email.ClientEmailFormTests` (valid persists / invalid rejected / empty allowed), `documents.tests.test_email.ResolvesClientEmailTests.test_resolves_saved_client_email_when_to_email_omitted` |

## Notes

- The existing `test_rectificativa_view._payload` helper gained a `metodo` key
  (default `"S"`) — the new required form field; existing happy-path behaviour is
  unchanged.
- Two migrations added: `clients/0002_client_email` (new field) and
  `submission/0002_alter_submissionattempt_status` (the `cancelled` choice — a
  choices-only `AlterField`, no DB schema change). Both generated/applied via
  `.venv`.
