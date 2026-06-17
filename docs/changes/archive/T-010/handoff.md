# T-010 Handoff — AEAT preproducción submission PoC (3 proofs)

**Status:** in-progress · **Branch:** `feat/T-010-aeat-preproduccion-poc` · **For:** the founder/developer with AEAT `preproducción` access
**Last commit:** `0fbc2b0` — update process *(work below is uncommitted on the branch; spec + scaffold are staged in the worktree)*

> **What's done:** the lane is started (spec `ready`, all rubric ✅), and the PoC
> harness is scaffolded and structurally verified. **What's left:** the three
> proofs themselves — they need a **qualified certificate valid for `preproducción`**
> and **live network access to the AEAT SOAP endpoint**, which the loop agent
> cannot supply. That's the entire reason for this handoff.

## 1. Acceptance criteria
> From `plan.md` Requirements R1–R4. The receiver verifies these by running the proofs.
- [x] Harness scaffolded under `poc/aeat-preproduccion/`; secrets git-ignored; skeletons fail cleanly without config. *(done this session — Operations box 1)*
- [ ] **R1 — cert auth:** client-cert TLS session to `preproducción` returns a service-level (non-auth-rejected) SOAP response.
- [ ] **R2 — XSD `alta`:** an `alta` record validates locally against the published XSD and AEAT returns per-record `Correcto`/`AceptadoConErrores` (not `Incorrecto` for a structural reason).
- [ ] **R3 — `huella` chain:** a second record carrying the first's `huella` is accepted with no `encadenamiento` error; both `huella` values recorded.
- [ ] **R4 — time-box gate:** each proof ends in a recorded PASS/FAIL in `design.md`; any blocker at the 2-session box triggers the AD-3 gateway-fallback via `/openup-request-input` rather than silent extension.
- [ ] AD-3 §3 of `docs/architecture-notebook.md` annotated with the running-proof outcome (on a clear verdict).

## 2. How to exercise it (test cases)
> Run from `poc/aeat-preproduccion/`. Full prereqs in its `README.md`.
1. **Supply credentials (no secrets in the tree):**
   ```bash
   export AEAT_CERT_PATH=/abs/path/cert.p12 AEAT_CERT_PASSWORD=...
   export AEAT_WSDL_URL='<current preproducción WSDL — resolve at run time, do NOT hard-code>' AEAT_NIF=<test issuer NIF>
   ```
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. **Wire `config.make_client()`** (currently raises `NotImplementedError` — the docstring gives the exact zeep + `requests_pkcs12` shape). This is Proof 1's first action.
4. `python proofs/proof1_auth.py` → handshake accepted + SOAP response ⇒ R1 PASS. Record in `design.md`.
5. `python proofs/proof2_alta.py` → per-record `Correcto`/`AceptadoConErrores` ⇒ R2 PASS. Record status, AEAT codes, and the record `huella`.
6. `python proofs/proof3_huella.py` → second (chained) record accepted, no `encadenamiento` error ⇒ R3 PASS. Record both `huella` values.
7. Write the verdict + AD-3 consequence in `design.md`; annotate AD-3 §3; tick the remaining Operations boxes in `plan.md`.
   - **Scaffold sanity (works now, no cert):** `python proofs/proof1_auth.py` → exits 2 with `BLOCKED: not yet wired` (proves the plumbing).

## 3. Troubleshooting
> From this session.
- **`preflight` blocked: "dependency T-007 is in-progress"** → root cause: T-007's *archived* `plan.md` had a stale `status: in-progress` (never bumped on completion), and `dep_satisfied` trusts the found plan over the roadmap (which says completed). **Fixed** by correcting `docs/changes/archive/T-007/plan.md` → `status: verified` (on this branch; propagates to main on completion). **T-009 has the same staleness** but blocks nothing today — left as a follow-up. Underlying gap: `/openup-complete-task` should bump archived `status` to a satisfied value (done/verified) on archive — framework fix, out of scope here.
- **Editing the spec was gate-blocked at first** → no `.openup/state.json` existed yet; the spec write only unblocks after `start-iteration` initializes state with `--plan` pointing at the plan path. (Expected for a freshly-promoted standard lane.)
- **No live-proof failures observed** — the proofs have not been run (no certificate/sandbox access).

## 4. Open questions
> Handed to the next owner. From `plan.md` Assumptions / `design.md`.
- **Certificate availability (the real blocker):** is an FNMT *test* cert obtainable for `preproducción`, or will the founder exercise a real qualified cert against the sandbox? Either works for the harness; one must be on hand to proceed. *(Assumption in `plan.md`, vetoable.)*
- **Current `preproducción` WSDL/XSD URLs + the autónomo obligation calendar (T-007 O-2):** resolve at run time, do not hard-code from memory — the spec dates moved.
- **If any proof blows the 2-session time box:** escalate the AD-3 **gateway-fallback** decision (founder call) via `/openup-request-input` — do not silently extend the box.
