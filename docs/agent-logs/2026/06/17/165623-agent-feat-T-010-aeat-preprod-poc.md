# Agent Run Log: T-010 AEAT Preproducción PoC

**Date**: 2026-06-17  
**Time**: 165623 UTC

## Run Metadata

| Field | Value |
|-------|-------|
| **Branch** | feat/T-010-aeat-preprod-poc |
| **Task** | T-010 — AEAT preproducción submission PoC (3 proofs) |
| **Phase** | construction |
| **Track** | standard |
| **Start** | 2026-06-17T16:36:08Z |
| **End** | 2026-06-17T16:56:23Z |
| **Commit** | b035e06 — feat(T-010): AEAT preproduccion PoC — 3 proofs pass, AD-3 BUILD-direct confirmed [T-010] |

## Files Changed

- `poc/aeat-preproduccion/config.py`
- `poc/aeat-preproduccion/alta_builder.py` (new)
- `poc/aeat-preproduccion/proofs/proof1_auth.py`
- `poc/aeat-preproduccion/proofs/proof2_alta.py`
- `poc/aeat-preproduccion/proofs/proof3_huella.py`
- `docs/changes/T-010/plan.md`
- `docs/changes/T-010/design.md`
- `docs/architecture-notebook.md`
- `docs/input-requests/archive/2026-06-17-aeat-preproduccion-access.md` (archived)
- `docs/status-notes/2026-06-17-T-010.md`

## Outcome

All three preproducción proofs PASS against live AEAT sandbox (prewww1.aeat.es, port SistemaVerifactuPruebas).

- **Proof 1** (cert mTLS auth): Accepted
- **Proof 2** (F1 alta): Validated vs XSD; accepted Correcto (CSV A-UBW7S9WQNYK338)
- **Proof 3** (huella hash-chain): Second record accepted Correcto (CSV A-54GWTLESJ6PV86), no encadenamiento error

## Decisions

- Resumed suspended lane (input-request answered: founder-real cert, resolve-WSDL-at-runtime, raise-fresh fallback; processed and archived)
- `config.make_client()` binds the preproducción port explicitly (WSDL's first port is production)
- AD-3 annotated with running-proof outcome
- R-03 high → managed
- BUILD-direct confirmed, gateway-fallback not triggered
