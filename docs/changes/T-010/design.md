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

## Proof outcomes (PENDING — require a founder-supplied certificate + live sandbox)

The three proofs cannot be executed by the loop agent: they need a **qualified
certificate valid for AEAT `preproducción`** and **network access to the live
SOAP endpoint** — credentials/access only the founder can supply. Handed off (see
the handoff brief) for a session that has both.

| Proof | Requirement | Status | Evidence (fill on run) |
|-------|-------------|--------|------------------------|
| 1 — cert auth | §R1 | ⏳ pending | handshake accepted? SOAP response? |
| 2 — XSD `alta` | §R2 | ⏳ pending | per-record status + AEAT error codes + record `huella` |
| 3 — `huella` chain | §R3 | ⏳ pending | both `huella` values; any `encadenamiento` error |

## AD-3 verdict (PENDING)

To be written once the three proofs resolve: **proceed with BUILD-direct** (all
cleared) **or** trigger the **gateway-fallback** decision via
`/openup-request-input` (any proof blocked at the 2-session time box). Until then,
AD-3 stays `accepted` on analysis only (T-007); the running-proof annotation in
`docs/architecture-notebook.md §3` is deferred to that verdict.
