# Run: feat/T-014-aeat-submission-adapter

**Task**: T-014 — AEAT submission adapter behind AD-3 interface  
**Branch**: feat/T-014-aeat-submission-adapter  
**Phase**: construction  
**Iteration**: 13  
**Track**: standard  

## Timeline
- **Start**: 2026-06-18T10:46:00Z
- **End**: 2026-06-18T10:57:45Z

## Commits
- `77ae5c5` docs(T-014): promote lane — author spec, board-visible [T-014]
- `03b9dea` feat(T-014): AEAT submission adapter behind AD-3 interface [T-014]

## Files Changed
**New Django `submission` app:**
- `gateway.py`
- `aeat_direct.py`
- `services.py`
- `models.py`
- `apps.py`
- `migrations/0001_initial.py`
- `management/commands/aeat_submit.py`
- `tests/factories.py`
- `tests/test_gateway.py`
- `tests/test_aeat_direct.py`
- `tests/test_services.py`

**Config & dependencies:**
- `config/settings.py` (register app + AEAT_* settings)
- `requirements.txt` (requests-pkcs12)

**Documentation:**
- `docs/changes/T-014/plan.md`
- `docs/changes/T-014/design.md`

## Key Decisions

- **AD-3 boundary**: `SubmissionGateway` interface + one direct mTLS-SOAP adapter productionizing the T-010 PoC transport; gateway-provider fallback can swap in unchanged.

- **Payload handling**: Submission payload re-wraps the stored bare `RegistroAlta` via `compliance.records.wrap_envelope` unmodified — never re-hashes/re-signs (record stays AD-2's).

- **Submission state**: Outcome stored in a new `SubmissionAttempt` model keyed to the record; record/invoice never mutated.

- **Retry logic**: Bounded transport-retry → `pending`; business `Incorrecto` never retried.

- **Feature flag**: `AEAT_SUBMISSION_ENABLED` config-read kill-switch (default off), preproducción-default endpoint.

- **Certificate access**: Cert material only via `certificates.services.get_cert_material`.

## Result

- 15 submission tests passing
- Full suite: 69 green
- `makemigrations --check` clean
- Fence + check-docs pass
- Flag-removal debt enqueued as T-019
