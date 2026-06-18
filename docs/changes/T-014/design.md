# T-014 — Design notes & in-flight decisions

## In-flight decisions

- **DD1 — Submission payload is the stored record, re-wrapped, never re-generated.**
  `compliance.services.generate_alta` persists `VerifactuRecord.xml` as the **bare
  `RegistroAlta`** element (optionally XAdES-signed), *not* the full
  `RegFactuSistemaFacturacion` envelope. The AEAT SOAP op expects the full envelope, so
  the adapter parses `record.xml` back to an element and calls
  `compliance.records.wrap_envelope([element], issuer_nif=record.issuer_nif,
  issuer_name=record.issuer_name)` to build the submittable `RegFactu`, then wraps that in
  the SOAP 1.1 envelope. The stored element is appended **unmodified** — the adapter never
  recomputes `huella` or re-signs, so an enveloped XAdES signature over the `RegistroAlta`
  subtree stays valid. This keeps record generation wholly inside AD-2 (T-013) and the
  adapter a pure transport (AD-3). Consuming `records.wrap_envelope` is a read-only use of
  the compliance builder, not a modification.

- **DD2 — Owner resolution chain: `record.invoice.series.owner`.** The certificate is keyed
  to a `User` (`certificates.UserCertificate.owner`, OneToOne); a record reaches its owner
  via `VerifactuRecord.invoice → invoicing.Invoice.series → invoicing.Series.owner`. The
  adapter pulls the user from the record and passes it to
  `certificates.services.get_cert_material(user)` — the sole sanctioned plaintext path.

- **DD3 — mTLS without a temp file.** `requests_pkcs12.Pkcs12Adapter(pkcs12_data=<p12
  bytes>, pkcs12_password=<passphrase>)` mounts on the `requests.Session`, so the decrypted
  PKCS#12 bytes from `CertMaterial` never touch disk (RGPD / least-privilege). Added
  `requests-pkcs12` to `requirements.txt`; the PoC used the same library.

- **DD4 — Outcome mapping.** `EstadoRegistro` (per-record) drives the verdict, falling back
  to `EstadoEnvio` (envelope-level): `Correcto` / `AceptadoConErrores` → `accepted`
  (the latter carries `CodigoErrorRegistro`); `Incorrecto` → `rejected`. A transport error
  (timeout / connection reset / HTTP ≥ 500) or an unparseable body → retry, then `pending`.
  A business `Incorrecto` is **never** retried (DD in spec — re-submitting an invalid record
  is wrong). The CSV (acceptance receipt) is stored on the attempt when present.

- **DD5 — Transport is injectable for tests.** `AeatDirectAdapter.__init__` takes an
  optional `transport` callable `(url, soap_bytes, *, cert_material) -> response_text`
  defaulting to the real `requests_pkcs12` session POST. Tests inject a fake transport and
  drive outcome-parsing / retry / pending without a real certificate or a live AEAT — the
  external call is the one thing the unit suite must not make (it is also flag-gated off in
  CI). The cert-gated preproducción smoke uses the real transport behind the env flag.

- **DD6 — `submit_record` short-circuits on the flag.** When `AEAT_SUBMISSION_ENABLED` is
  falsey the orchestration returns a `disabled` outcome **before** resolving cert material or
  opening a session — so CI and local never reach the tax authority, and no
  accepted/rejected/pending attempt is written for a disabled call.

## Open for review

- **SIF producer identity** stays the issuer (T-013 DD10) — FacturaSimple's own SaaS fiscal
  identity as `SistemaInformatico` producer is a pre-production launch constant, out of
  T-014 scope (recorded as a spec assumption).
- **Async retry of `pending` attempts** — T-014 persists `pending`; a scheduled re-drive of
  pending attempts (cron / management command) is deferred (no broker in scope).

## Completion grade (step 1a/1b — graded against the diff + green suite)

Requirements (`git diff main...HEAD`, 69 tests green):

- ✅ **R1** interface — `submission/gateway.py` `SubmissionGateway` ABC + `SubmissionOutcome`;
  `services.submit_record` depends only on the interface (grep: `AeatDirectAdapter` appears
  only as the def and the `_default_gateway` factory); `test_gateway` conformance.
- ✅ **R2** mTLS via sanctioned path — `aeat_direct.submit` → `certificates.services.get_cert_material`;
  no `certificates.crypto` import in non-test code (grep clean);
  `test_submit_uses_stored_cert_material_via_service` + `test_missing_certificate_propagates_and_skips_transport`.
- ✅ **R3** SOAP wrap + parse — `_build_soap_payload` (RegFactu→SOAP) + `parse_response`/`outcome_from_response`;
  `ResponseParsingTests` (Correcto→accepted+CSV, AceptadoConErrores→accepted+code, Incorrecto→rejected+code).
- ✅ **R4** persist SubmissionAttempt, no mutation — `models.SubmissionAttempt` + `services._persist`;
  `test_accepted_persists_attempt_and_leaves_record_untouched` (record.xml unchanged).
- ✅ **R5** retry→pending, no-retry-on-rejection — `services.submit_record` loop;
  `test_persistent_transport_failure_degrades_to_pending` (4 calls, pending, retries=3),
  `test_rejection_is_not_retried` (1 call), `test_transient_failure_then_acceptance` (retries=1).
- ✅ **R6** env-config + preproducción default + flag — `settings.AEAT_*`;
  `test_disabled_short_circuits_and_writes_no_attempt`; default endpoint = prewww1 (preproducción).

**Success-measure instrumentation (1b):** ✅ `SubmissionAttempt.status` is written on every
non-disabled submission (`services._persist`) — a `GROUP BY status` count is directly available.
Read-back: **2 weeks after the submission flag is enabled in beta**.

All requirements ✅ — no gaps.
