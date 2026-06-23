# Exploration: Is per-record XAdES signing load-bearing for the current Verifactu flow?

**Started:** 2026-06-23
**Question:** Does our Verifactu submission flow actually consume the per-record
XAdES signature produced by `compliance/signing.py::sign_record()`, or is the
user certificate only needed for channel (mTLS) authentication to the AEAT
webservice?

## Context

This is the **Q0 premise check** sitting *above* the browser-side-signing
exploration. The security-first revision of
[2026-06-23-browser-side-signing.md](2026-06-23-browser-side-signing.md)
scoped a dual-track signing iteration (AutoFirma + browser JS signing) to keep
the private key off the server. The
[legal finding](2026-06-23-legal-qscd-finding.md) then resolved the QSCD
blocker favourably **and dropped a premise-level flag**: in VERI\*FACTU mode the
AEAT FAQ states no per-record electronic signature is required at all — integrity
comes from the hash chain (`huella`/encadenamiento) plus reliable remission, and
the certificate authenticates the *submission channel*.

If our code never actually submits a signature, the entire browser-side-signing
exploration collapses to a no-op for the current flow. If it does, it sharpens
into a real iteration. This file settles that with code evidence before any
signing iteration is scoped.

## Notes

### Verdict: (B) — per-record signing is GROUNDWORK, not load-bearing today

The XAdES signature output is **not submitted to AEAT** in any production flow.
What reaches AEAT is the bare `RegistroAlta`/`RegistroAnulacion` (huella chain
included) over an mTLS channel authenticated with the user's certificate. The
signing infrastructure exists, is well-built, and is exercised only by tests.

### Evidence (code-traced)

1. **`sign_record()` returns an XAdES-BES enveloped XML string** over the
   registro element — `compliance/signing.py:36-51`.

2. **No production caller passes a signer.** `generate_alta()` /
   `generate_anulacion()` take an optional `signer=None`; with none, the record
   is serialized **unsigned** and persisted with `signed=False`
   (`compliance/services.py:60-101`, esp. 96-100, 116-117; anulación 150-152,
   202-204). Every production call site omits the signer:
   - `invoicing/views.py:136`, `invoicing/views.py:386` (generate_alta)
   - `invoicing/views.py:314-316` → `annul_invoice` → `generate_anulacion(signer=None)`
   - `invoicing/services.py:140` (`issue_rectificativa`) forwards `signer=None`
     by default.
   The **only** callers that pass `signing.signer_for_user(...)` are tests
   (`compliance/tests/test_signing.py:41,49,74`; `test_rectificativa.py:35`).

3. **The submission adapter appends `record.xml` unmodified** and never
   re-signs — `submission/aeat_direct.py:47-65` (`_build_soap_payload`, parse at
   :53, wrap unmodified at :54-55). Since production records are unsigned, the
   SOAP body carries no `<Signature>`.

4. **The certificate is used exclusively for mTLS client auth** —
   `submission/aeat_direct.py:137-167`, `Pkcs12Adapter(pkcs12_data=...,
   pkcs12_password=...)` at :151-154. That is the certificate's only role in the
   submission path.

5. **`build_registro_alta()` has the huella/Encadenamiento block but no
   signature field** — `compliance/records.py:129-207` (encadenamiento
   :193-201). The signature, when produced, is enveloped by signxml, not a
   schema field.

6. **Tests confirm the negative:** submission factories build unsigned records
   (`submission/tests/factories.py:16-24`); the SOAP test asserts the envelope
   wrapper only and **no test asserts a `<Signature>` in the body**
   (`submission/tests/test_aeat_direct.py:81`).

7. **Design docs already documented this as optional:** T-013 DD6 — "with none,
   the record persists unsigned (`signed=False`)"; T-014 DD1 — adapter appends
   "unmodified", never re-signs (so a signature *would* stay valid if present,
   but none is generated).

### What this means for the browser-side-signing exploration

The browser-side-signing exploration's premise — "move the signing step into the
browser so the key never reaches the server" — assumes a signing step exists on
the submission critical path. **For the current VERI\*FACTU flow, it does not.**
The server-held key is consumed by `Pkcs12Adapter` for mTLS, *not* by
`sign_record()`. So:

- The **private-key-custody problem is real but its locus moves**: the key the
  server decrypts is used for the TLS handshake to AEAT, not for XAdES signing.
  Browser-side XAdES signing does **not** remove the server's need to hold key
  material, because mTLS to AEAT happens server-side. This is the load-bearing
  finding the browser exploration was missing.
- Therefore the dual-track signing iteration (AutoFirma + browser JS XAdES) is
  **premature/misaimed for the current flow** — it would protect a signature
  nobody submits while leaving the real key-custody surface (mTLS) untouched.

### Caveat / scope boundary of this verdict

This verdict is about the **current** flow only. The signing code is plausible
groundwork for a future **NO-VERI\*FACTU** mode (records stored in the SIF or
served on *requerimiento*), where Orden HAC/1177/2024 *does* mandate a XAdES
signature from a qualified certificate (per the legal finding). It is not dead
code to delete reflexively — it is unwired capability whose trigger condition
(NO-Verifactu mode) the product does not target today.

## Options Considered

- **Option 1 — Treat signing as confirmed groundwork; pause the
  browser-signing iteration.** Park the dual-track signing work; redirect the
  key-custody concern to where the key is actually used (mTLS transport). Pro:
  stops a misaimed iteration; focuses effort on the real surface. Con: leaves
  `signing.py` as unwired code (documentation debt risk).

- **Option 2 — Re-scope the privacy goal around the mTLS key, not the signature.**
  The founder's "never store the private key/passphrase server-side" directive
  actually bites on the *transport* certificate. Explore whether AEAT submission
  can be brokered without the server holding decryptable key material (e.g.
  client-side submission, a thin signing/transport proxy, or ephemeral
  per-session key handling). Pro: targets the genuine residual surface. Con:
  harder problem; AEAT mTLS from a browser is constrained.

- **Option 3 — Do nothing; keep building.** Leave both the signing groundwork
  and the server-side mTLS custody as-is. Pro: zero cost now. Con: leaves the
  founder's security-first directive unmet and a misleading exploration on record
  implying browser signing solves custody.

## Open Questions

- Can AEAT VERI\*FACTU submission be performed **without the server holding
  decryptable key material** for mTLS? (The real custody question. Browser-origin
  mTLS to `*.aeat.es` is the constraining unknown.)
- Should `compliance/signing.py` be explicitly **labelled as NO-Verifactu
  groundwork** (docstring + AD-3 note) so it is not mistaken for a live
  submission dependency?
- Does the project roadmap actually intend a NO-Verifactu mode? If never, is the
  signing code worth retaining at all, or should it move behind a clearly-marked
  future-mode flag?

### Product-manager challenge pass

(role hat: `.claude/teammates/product-manager.md` — no team deployed)

- **Pushback — the parent browser-signing exploration optimised the wrong
  surface.** Its security-first revision ranked AutoFirma/browser options to keep
  the key off the server, but the code shows the server's key use is **mTLS
  transport, not XAdES signing**. Moving signing to the browser changes nothing
  about the dominant custody surface. The whole dual-track scope is built on an
  unverified premise this Q0 check now falsifies. Accepted — folded into "What
  this means" above; the browser-signing disposition must be superseded.

- **Pushback — "signing is unused → delete it" would be wrong.** The cheap
  reflex (rip out `signing.py`) ignores that it is plausibly NO-Verifactu
  groundwork mandated by Orden HAC/1177/2024. Deleting it trades a documentation
  problem for a re-implementation cost later. Accepted — verdict explicitly scoped
  to "current flow only"; Option to label, not delete.

- **Complement — the real privacy win the founder wants lives at the transport
  layer.** The RGPD data-minimisation argument from the parent exploration still
  holds, but the thing to minimise is the **mTLS certificate custody**, not the
  signature. This reframes the next iteration target. Accepted — Option 2.

- **Refine — sharpen the parent exploration's "where this goes next."** Its
  disposition ("run a browser-XAdES PoC, scope dual-track") should be **shelved
  pending a NO-Verifactu decision**, and replaced by the transport-custody
  question. Accepted — see disposition.

- Disposition per challenge: all four accepted into the notes/options above; none
  rejected. The parent browser-signing exploration's "where this goes next" is
  hereby superseded for the current flow.

## Where this goes next

→ quick-task — Record the verdict where it counts: (1) add a brief
"NOT on the current VERI\*FACTU submission path — NO-Verifactu groundwork"
note to `compliance/signing.py` and AD-3 in the architecture notebook, and
(2) annotate the parent `2026-06-23-browser-side-signing.md` that its dual-track
signing scope is **shelved** because per-record signing is not load-bearing today
and the real key-custody surface is server-side mTLS transport. The transport-
custody question (Option 2) is logged as an open question for a future
`/openup-explore`, not promoted to delivery yet.
