# T-013 — Design notes & in-flight decisions

## In-flight decisions

- **DD1 — Versioned module, lazy public surface.** `compliance/__init__.py` exposes
  `MODULE_VERSION` (literal) + the public verbs (`generate_alta`,
  `generate_anulacion`, `validate_issuable`) via PEP 562 `__getattr__` lazy import.
  This keeps the AD-2 public surface importable at Django app-load time **without**
  pulling the ORM models in before the app registry is ready (the classic
  `AppRegistryNotReady` trap). Callers never import the private submodules.
- **DD2 — Per-issuer chain lock row (`IssuerChain`).** The Verifactu chain spans
  **all** of an issuer's numbering series, so — unlike T-012's per-`Series`
  high-water lock — the serialization point is keyed on the issuer NIF.
  `services._lock_chain` does `get_or_create` + `select_for_update` on the
  `IssuerChain` row for the generation's duration, so concurrent generations can't
  both read the same tail and fork the chain (AD-6/Q-1). Mirrors T-012's numbering
  pattern at the issuer grain.
- **DD3 — `huella` ported verbatim from the T-010 PoC.** `records.compute_huella`
  reproduces the exact field order/format AEAT accepted live (`preproducción`
  proofs 2 & 3). A unit test re-derives the SHA-256 over the spec concatenation
  independently and asserts equality — so a future field-order regression fails.
  `compute_huella_anulacion` uses the annulment field order (annulled-invoice
  identity, no TipoFactura/amounts).
- **DD4 — `ImporteTotal` excludes IRPF.** The Verifactu importe is `base + IVA`;
  the IRPF retention (a payer-side withholding) is **not** part of it. `generate_*`
  persists `cuota_total = iva_total`, `importe_total = taxable_base + iva_total`,
  matching the PoC's 100→121 record.
- **DD5 — Issuer identity is passed in, not read off the invoice.** T-012's
  `Invoice`/`Series` carry no issuer NIF/name (the `huella`'s `IDEmisorFactura`).
  Rather than invent a business-profile model here, `generate_alta` takes
  `issuer_nif`/`issuer_name` explicitly and `validate_issuable` requires them. The
  eventual caller (issue flow / T-014) supplies them; a business-profile source is
  a separate concern. **Open for review** — if a profile model lands, wire it here.
- **DD6 — Signing is injected, not embedded.** `services.generate_*` accept an
  optional `signer` callable (`element -> signed_xml_str`); with none, the record
  persists unsigned (`signed=False`) with identical chain/persist semantics. This
  keeps the transactional core free of any XML-DSig dependency and lets the XAdES
  signer (`compliance/signing.py`) land independently without touching `services`.
- **DD7 — stdlib `ElementTree` for building (no premature lxml dep).** Record
  construction uses `xml.etree.ElementTree` — no third-party XML runtime dep at the
  build layer. lxml + the XAdES library are added **with** the signing box, where
  C14N + XSD validation actually need them (the spec's open architect-assumption).

## Exempt-rate Desglose — known simplification (XSD-gated)

`records._desglose` emits one `DetalleDesglose` per IVA rate group. For rate > 0 it
writes `CalificacionOperacion=S1` + `TipoImpositivo` + `CuotaRepercutida`. For an
exempt group (rate 0) it writes `CalificacionOperacion=S2` + base only. The exact
exempt code (S2 vs an `OperacionExenta`/`CausaExencion` block) is **legal detail that
must be validated against the published XSD** — deferred to the signing/validation
box where the XSD is vendored. The structural shape (one detalle per group, bases/cuotas
matching `invoicing.calc`) is tested now; XSD-conformance is not yet asserted.

## Security note — XML parsing (carry into T-014 / signing)

`records.py` only **builds** XML (no parsing of untrusted input). The tests parse
**self-generated, trusted** XML. When inbound/untrusted XML is parsed — AEAT
responses (T-014), or signature/XSD verification of externally-supplied records —
use **`defusedxml`** (stdlib parsers are open to XXE / billion-laughs). Flagged by
the security hook during this task.

## Handoff — what remains (external-dependency boundary)

Completed this cycle (dependency-free): Operations 1, 2, 3, 5, 6 — scaffold + model
+ migration + settings, validation gate, record/huella builders, transactional
chain + persist for alta and anulación. 11 compliance tests green (req 1, 2, 4,
5-linkage, 7 + Desglose structure); full suite 48 green.

Remaining (Operations 4 + tester remainder), all gated on external resources:

1. **Install deps** — add `lxml` + a XAdES/XML-DSig library (e.g. `signxml` or
   `xmlsec`) to `requirements.txt`; pin per the spec's open architect-assumption.
2. **`compliance/signing.py`** — XAdES-enveloped signature over a built record using
   `certificates.services.get_cert_material(invoice.series.owner)`, plus a verify
   helper. Wire it as the `signer` callable into `generate_alta`/`generate_anulacion`
   (the seam already exists — DD6). Test signature verifies + fails on one-byte
   tamper (Requirement 6). Use a **self-signed fixture cert** (never the founder's
   real cert — T-010 DD2).
3. **Vendor the Verifactu XSD** — the PoC kept it git-ignored under
   `poc/aeat-preproduccion/secrets/wsdl/`; vendor a copy under
   `compliance/tests/fixtures/` and assert a generated `RegistroAlta` validates
   (Requirement 3 XSD-conformance) — including resolving the exempt-rate
   `CalificacionOperacion` code above.
4. **Postgres-gated fork-safety test** — a true concurrent `generate_alta` race
   serialises into a linear chain (Requirement 5, second clause). Mirror T-012's
   `@skipUnlessDBFeature("has_select_for_update")` `ConcurrentIssuanceTests`.

Resume point: the worktree `../es-invoices-T-013` (lease + `.openup/state.json`
live there); first unchecked Operations box = the signing box.
