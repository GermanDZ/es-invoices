# T-013 Handoff — Compliance/Verifactu module: record gen + hash-chain + XAdES

**Status:** in-progress · **Branch:** feat/T-013-compliance-verifactu · **For:** next developer/tester (resume in the worktree `../es-invoices-T-013`)
**Last commit:** 9a063d7 — feat(compliance): Verifactu record gen + huella chain + per-issuer lock [T-013]

This cycle landed the dependency-free core (Operations 1, 2, 3, 5, 6). The remaining work (Operation 4 signing + the tester remainder) is gated on external resources — install libs + vendor the XSD. The `services` layer already exposes a `signer` injection seam, so signing drops in without touching the transactional core.

## 1. Acceptance criteria
> The seven plan.md requirements. Checked = verified green this cycle; unchecked = remaining (see §4 + design.md §Handoff).
- [x] R1 — Versioned module interface: `compliance.MODULE_VERSION` + public verbs reachable without importing private submodules (`test_interface`).
- [x] R2 — Legal-field validation blocks malformed records, persists nothing (`test_validation`).
- [~] R3 — `RegistroAlta` Desglose has one `DetalleDesglose` per IVA rate group matching `invoicing.calc` (`test_records`). **XSD-conformance assertion NOT yet done** — needs the vendored XSD.
- [x] R4 — `huella` reproduces the AEAT spec concatenation byte-for-byte; first record marks `PrimerRegistro=S` (`test_records`).
- [~] R5 — Chain linkage: each record references the prior record for the issuer (`test_chain`). **Fork-safety under a true concurrent race NOT yet tested** — Postgres-gated, see §4.
- [ ] R6 — XAdES-enveloped signature verifies against the cert and fails on tamper. **Not started** (Operation 4).
- [x] R7 — Annulment record references the original `IDFactura` and chains on the tail (`test_chain`).

## 2. How to exercise it (test cases)
> The worktree has no local `.venv`; use the main repo's interpreter.
1. `VPY=/Users/germandz/personal-code/ai-dev-framework/es-invoices/.venv/bin/python` then `cd ../es-invoices-T-013`
2. `$VPY manage.py test compliance -v2` → 11 tests OK
3. `$VPY manage.py test` → full suite 48 OK (1 skip = T-012 Postgres-gated concurrency test)
4. `$VPY scripts/openup-fence.py check --task-id T-013` → "18 changed file(s) within lane"
5. `$VPY scripts/openup-spec-scenarios.py check docs/changes/T-013/plan.md` → exits 0

## 3. Troubleshooting
> Failure modes hit during this cycle and their fixes.
- **`AppRegistryNotReady` if the app `__init__` imports models** → the public verbs are resolved lazily via PEP 562 `__getattr__` in `compliance/__init__.py`; `MODULE_VERSION` is a literal there. Do not add eager `from .models import ...` to `__init__`.
- **`ModuleNotFoundError: No module named 'django'` in the worktree** → the worktree has no `.venv`; run Django with the main repo's interpreter (see §2 step 1).
- **Write-fence "OUT OF LANE"** → the claim's `touches` is `compliance/,config/settings.py,requirements.txt` (re-claimed with `--force --touches`, since the spec frontmatter carries no `touches`). Adding files outside these needs a re-claim. `docs/project-status.md` is a derived view (T-024) — do NOT hand-edit it on the branch; it was reverted this cycle.
- **`merge`/commit message rejected** → commit type must be one of build/chore/ci/docs/feat/fix/perf/quick/refactor/revert/style/test (no `merge` type); the spec was landed to trunk with a `docs(T-013): ...` merge message.

## 4. Open questions
> Decisions handed to the next owner.
- **XAdES library choice** (spec architect-assumption, still open): pin `lxml` + one of `signxml` / `xmlsec` in `requirements.txt`. xmlsec needs the native `libxmlsec1`; signxml is pure-Python over lxml. Pick and record in design.md.
- **Issuer identity source** (design.md DD5): `generate_alta` takes `issuer_nif`/`issuer_name` explicitly because T-012's `Invoice`/`Series` carry no issuer fiscal identity. If a business-profile model lands, wire it in; otherwise the caller (issue flow / T-014) supplies them.
- **Exempt-rate `CalificacionOperacion` code** (design.md): the exempt (rate 0) branch currently writes `S2` + base only; the exact code (S2 vs an `OperacionExenta`/`CausaExencion` block) must be validated against the published XSD when it is vendored.
- **`defusedxml` for untrusted XML**: `records.py` only builds XML (safe); when the signing/verification or T-014 response-parsing parses untrusted XML, use `defusedxml` (XXE / billion-laughs). Flagged by the security hook this cycle.
- **Vendor the Verifactu XSD**: the PoC kept it git-ignored under `poc/aeat-preproduccion/secrets/wsdl/`; vendor a copy under `compliance/tests/fixtures/` for the R3 XSD-conformance test.
