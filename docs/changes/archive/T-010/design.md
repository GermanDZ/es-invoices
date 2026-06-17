# T-010 — AEAT preproducción submission PoC: design & proof log

> Records the per-proof outcomes and the consequent AD-3 verdict. The three
> proofs are defined authoritatively in `docs/changes/archive/T-007/design.md §2`.

## Decisions / notes

- **DD1 — Throwaway harness, isolated under `poc/aeat-preproduccion/`.** The PoC
  is disposable evidence, not the production adapter (T-014). Kept out of any app
  tree (the repo is greenfield; Django arrives with T-012). Deleted once the
  verdict below is recorded and AD-3 is annotated.
- **DD2 — Secrets never in the tree.** The qualified certificate is read from an
  env-injected local path; `.gitignore` blocks `*.p12/*.pfx/*.pem/*.key/*.cer/*.crt`
  and the `secrets/` + `captured/` dirs. RGPD surface even against `preproducción`.
- **DD3 — Endpoints/WSDL resolved at run time, not hard-coded.** The current
  `preproducción` WSDL/XSD URLs must be looked up at execution (the spec moved —
  T-007 O-2). The URL actually used is recorded with the proof outcomes below.

## Scaffold status (Operations box 1 — DONE 2026-06-17)

- `poc/aeat-preproduccion/` created: `README.md` (run instructions + prereqs),
  `requirements.txt` (AD-5 toolchain), `config.py` (cert + endpoint + session
  resolution, fails loudly on missing config), and `proofs/proof{1,2,3}_*.py`
  skeletons.
- `.gitignore` extended to block all certificate/key material and credentialed
  captures. Verified: `git check-ignore` confirms `*.p12`/`*.pem` are ignored;
  no secret is tracked.
- Skeletons run and fail **cleanly** with a `BLOCKED: not yet wired` message when
  no cert/endpoint is configured (verified `proof1_auth.py` → rc 2). This proves
  the package structure + config plumbing are sound and ready for wiring.

## Run configuration (resolved 2026-06-17, DD3)

Input-request `2026-06-17-aeat-preproduccion-access.md` answered + archived:

- **Certificate (Q1 = `founder-real`)** — founder's personal FNMT qualified cert,
  `poc/aeat-preproduccion/secrets/verifactu.p12` (git-ignored). Passphrase via
  `AEAT_CERT_PASSWORD` in a git-ignored local `.env`. Execution model:
  founder-authorized local runs (2026-06-17); the private key is read only by the
  local proof process — never in agent context or the repo.
- **WSDL/XSD (Q2 = resolve at run time)** — downloaded from the AEAT *información
  técnica* page base
  `https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/`
  (`SistemaFacturacion.wsdl` + `SuministroInformacion/SuministroLR/RespuestaSuministro/ConsultaLR/RespuestaConsultaLR.xsd`),
  staged under `secrets/wsdl/` (git-ignored) and loaded locally (relative imports).
- **Endpoint** — preproducción port `SistemaVerifactuPruebas` →
  `https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP`.
  **Gotcha recorded in `config.py`:** the WSDL's first port is PRODUCTION
  (`www1`); `make_client()` binds the `Pruebas` port explicitly so test data
  never hits production.
- **Time-box fallback (Q3 = `raise-fresh`)** — on a blocked proof, raise a new
  input-request rather than auto-triggering the gateway fallback.

## Proof outcomes

| Proof | Requirement | Status | Evidence |
|-------|-------------|--------|----------|
| 1 — cert auth | §R1 | ✅ **PASS** (2026-06-17) | Raw client-cert mTLS POST of a minimal envelope → **HTTP 200** SOAP Fault `Codigo[4102] El XML no cumple el esquema. Falta informar campo obligatorio.: Cabecera`. TLS handshake accepted (cert authenticated) and the VERI*FACTU service answered at schema-validation level — auth + service-reach proven; minimal payload rejected pre-persistence (no record created, nothing to annul). |
| 2 — XSD `alta` | §R2 | ✅ **PASS** (2026-06-17) | Built one F1 `alta`, validated locally vs XSD (**PASS**), submitted → **HTTP 200 `EstadoEnvio: Correcto` / `EstadoRegistro: Correcto`, CSV `A-UBW7S9WQNYK338`**. AEAT registered the record. |
| 3 — `huella` chain | §R3 | ✅ **PASS** (2026-06-17) | Second `alta` chained via `Encadenamiento/RegistroAnterior` (prior `huella`) → **`Correcto`, CSV `A-54GWTLESJ6PV86`, no `encadenamiento` error**. huellas: `0A8DE84F…608C7` → `BC953112…316D7`. |

### Iteration evidence (the error codes that shaped the conformant record)

The path to a `Correcto` exercised AEAT's real business-rule + census layers —
proof the integration is genuinely understood, not just structurally well-formed:

- **`4102`** (Proof 1 minimal probe) — `Falta … Cabecera`: confirmed auth + service reach.
- **`1189`** — F1 requires a `Destinatarios` block. Added it.
- **`1239`** — destinatario NIF `89890001K` *not in census*: AEAT census-validates
  recipients. Resolved with a real census-identified NIF.
- **Real-NIF confirmation** — destinatario `A82037292` (MEDIA MARKT SATURN SA, a
  public census-identified company) → **no 1239**; record `AceptadoConErrores`
  **`2007`** *("no debe informarse como primer registro, existen facturas …")* — i.e.
  AEAT had **persisted our earlier records** for this obligado+SIF, so `PrimerRegistro`
  no longer applies. Positive evidence of chain-state persistence; the chained
  Proof-3 record under the same run returned **`Correcto`, CSV `A-4PSJTZGDMUZ9Z2`**.
- **`3000`** (duplicado) — surfaced a harness nit (second-granularity `NumSerie`
  collision on same-second runs); fixed with microsecond granularity. Not an AEAT gap.

`huella` algorithm validated end-to-end against the published spec
(`IDEmisorFactura&NumSerieFactura&FechaExpedicionFactura&TipoFactura&CuotaTotal&ImporteTotal&Huella&FechaHoraHusoGenRegistro`,
UTF-8 → SHA-256 → upper hex); AEAT accepted both first and chained huellas.

## AD-3 verdict — ✅ PROCEED WITH BUILD-DIRECT (2026-06-17)

All three proofs cleared against live AEAT `preproducción`, **inside the 2-session
time box**:

1. **Auth** — the founder's qualified certificate authenticates over mutual TLS to
   the VERI\*FACTU preproducción service.
2. **Conformant submission** — a self-built F1 `alta` validates locally against the
   published XSD and is accepted by AEAT (`Correcto` + CSV).
3. **Hash-chaining** — a second record chained on the prior `huella` is accepted
   with no `encadenamiento` error.

**Consequence:** residual **R-03** (the highest live technical risk — "can we
actually submit to AEAT ourselves?") collapses from *high* to *managed*. The
BUILD-direct **AD-3** decision is now backed by a running proof; the
gateway-fallback (Q3 `raise-fresh`) is **not** triggered. Broad Construction build
(T-013 compliance module, T-014 submission adapter) may proceed on the direct
integration. This throwaway harness is retained only as evidence and deleted per
DD1 once AD-3 §3 is annotated.

## Requirement verification (completion grade, 2026-06-17)

Graded against the actual diff + live run outcomes:

- ✅ **R1 — Certificate auth (Proof 1).** `proofs/proof1_auth.py` +
  `config.make_session()` → HTTP 200 SOAP response from `prewww1.aeat.es`; TLS/cert
  handshake accepted (not an auth rejection). Logged.
- ✅ **R2 — XSD-conformant `alta` (Proof 2).** `alta_builder.build_regfactu` +
  `validate_local` (local XSD PASS) + `proofs/proof2_alta.py` submission →
  `EstadoRegistro: Correcto`, CSV `A-UBW7S9WQNYK338`. Error codes 1189/1239 captured
  en route. Not `Incorrecto` for a structural reason.
- ✅ **R3 — `huella` hash-chain (Proof 3).** `compute_huella` (spec field order) +
  `Encadenamiento/RegistroAnterior` + `proofs/proof3_huella.py` → second record
  `Correcto`, CSV `A-54GWTLESJ6PV86`, **no** encadenamiento error; both huellas recorded.
- ✅ **R4 — Time-box gate honored.** All three proofs cleared within the 2-session
  box; explicit per-proof verdict + AD-3 consequence recorded above; Q3 `raise-fresh`
  fallback documented (not triggered — no blocker reached).

**Rollout / Success Measures:** both `n/a` per spec (internal feasibility PoC; the
binary proof outcome *is* the deliverable, read back immediately) — steps 1b/4a n/a.
