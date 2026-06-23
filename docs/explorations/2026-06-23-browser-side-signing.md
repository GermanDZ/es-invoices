# Exploration: Browser-side XAdES signing to avoid server-held private keys

**Started:** 2026-06-23
**Question:** Can we move the XAdES signing step into the browser so the user's
private key never reaches the server, without breaking the submission flow?

## Context

Task T-011 designed the current model: user uploads their AEAT qualified
certificate (PKCS#12 / P12 + passphrase) → server encrypts both at rest (AES-256-GCM,
`certificates/crypto.py`) → `compliance/signing.py` decrypts on submission to sign
`RegistroAlta`/`RegistroAnulacion` records with XAdES-BES before sending the
SOAP call to AEAT.

The security property the current model delivers: private key encrypted at rest,
server *can* decrypt it (it has the `CERT_ENCRYPTION_KEY`). The property the user
wants: private key *never transits the server wire or database at all*.

Architecture decision AD-3 says "each user supplies their own qualified AEAT
certificate, which we **store securely** (encrypted at rest)." This exploration
asks whether we can satisfy the submission requirement without that storage.

Related: `docs/architecture-notebook.md` AD-3, AD-5; T-011 design.md DD3/DD4;
`compliance/signing.py` `sign_record()`.

## Notes

### What the signing step actually does

`compliance/signing.py::sign_record(element, cert_material)` does exactly:
1. Loads the P12 (private key + certificate chain) from server-decrypted bytes.
2. Serialises the key to PEM (in-process, never logged).
3. Calls `XAdESSigner().sign(...)` from `signxml` — produces XAdES-BES enveloped
   XML-DSig over the `RegistroAlta` element.
4. Returns the signed XML string, which the AEAT SOAP adapter then wraps.

The server builds the element first (`compliance/records.py`), signs it, then
submits. The signing is the *only* step that needs the private key.

### What the browser can do today

**Web Crypto API** — present in all modern browsers, available only in
HTTPS/localhost contexts. Relevant operations: `importKey`, `sign` (RSA-PKCS1-v1_5,
RSA-PSS), `SubtleCrypto.exportKey`. Crucially supports `extractable: false` on
import — the private key is then usable for `sign()` calls but cannot be exported
by any JS call, including malicious JS in the same origin.

**PKCS#12 parsing in the browser** — not natively supported; requires a library.
Two viable options:

- `pkijs` (PKI.js, `@peculiar/webcrypto`) — a full ASN.1/CMS/PKCS#12 parser
  built on top of Web Crypto, well-maintained, actively used in browser PKI apps.
  Can parse P12, extract private key as a non-extractable Web Crypto `CryptoKey`.
- `node-forge` — older, pure-JS, does parse P12 and can sign, but its signing
  is its own RSA implementation (not delegating to Web Crypto), which means the
  key material is a JS object that *is* readable by any same-origin script.
  **node-forge is weaker for the goal we care about; prefer pkijs.**

**XAdES in the browser** — `xadesjs` (also `@peculiar/xadesjs`) implements
XAdES-BES/EPES on top of Web Crypto and pkijs. Actively maintained, used in
production by e-government portals in several EU countries. Produces the same
XAdES-BES enveloped signature that `signxml` produces on the server.

### The flow under browser-side signing

```
Server                          Browser
------                          -------
Build RegistroAlta XML  ──────> Unsigned XML
                                + (user loads P12 if not cached)
                                + Sign via xadesjs + pkijs
                    <────────── Signed XML
Wrap in SOAP
Submit to AEAT
Store outcome
```

Server still needs the *certificate* (public parts only — to validate chain at
startup and to attach the `X509Data` in the SOAP header). The private key never
leaves the browser.

### Options for where the key lives between sessions

**Option A — No browser storage (session-only P12 load)**
User selects their P12 file from disk each time they open a submission session.
Browser parses and holds the key in memory only; on page unload it is gone.
Maximum privacy, worst UX: every session requires a file-pick interaction.

**Option B — Non-extractable Web Crypto key in IndexedDB**
On first use the user imports their P12; `pkijs` extracts the private key and
imports it into Web Crypto with `extractable: false`; the resulting `CryptoKey`
object is stored in IndexedDB (the raw key bytes never exist in JS land at this
point). On future sessions the browser loads the `CryptoKey` directly — no P12
re-upload needed. Downside: the key is tied to that browser profile; a new browser
or incognito tab requires re-import. Clearing site data deletes it.

**Option C — Hybrid: browser holds key, server holds cert chain only**
Server stores *only* the public certificate (DER/PEM, no passphrase, no private
key) — enough to attach to SOAP headers and to verify the chain. User keeps their
P12 locally. This is a clean split: server is not a credential custodian at all,
just a submission proxy.

This is the cleanest model for the privacy goal. Server storage changes from
`encrypted_cert_blob + encrypted_passphrase` to `public_cert_bytes` (no
encryption needed — it's a public object).

**Option D — AutoFirma (Spain's @firma native signing client)**
The Spanish government provides AutoFirma: a local signing app installable on
Windows/macOS/Linux. The AEAT's own citizen portal (sede.agenciatributaria.gob.es)
uses AutoFirma for signing. A `miniapplet.js` or `autofirma.js` client sends
the to-be-signed data to the local app over a local HTTPS endpoint; the local
app accesses hardware tokens, macOS Keychain, Windows CertStore, or P12 files,
signs, and returns. Private key never leaves the user's machine or hardware token.

Pros: supports hardware tokens (the highest-assurance qualified certs live on
smart cards); signing app already trusted by many AEAT users; handles the
PKCS#12/P12 import problem. Cons: dependency on a desktop app (mobile/tablet
users blocked); requires app installation (adds friction); local HTTP endpoint
is a non-trivial security surface; doesn't work in sandboxed browser tabs without
a browser extension.

### The unattended-operation problem

DD4 in T-011 design.md explicitly says: "The P12 passphrase is stored encrypted
so the T-014 submission adapter can run unattended." UC-002 alternative flow 2a
queues records and retries on transport failure — without user presence.

Browser-side signing fundamentally breaks unattended operation: if the user
closes their browser, no retry can proceed. Options:

1. **Accept the constraint**: drop the retry queue; instead surface failures
   immediately in the UI for the user to resubmit. Verifactu records can be
   re-signed and resubmitted without loss of chain integrity (the hash chain
   links to the *record* not the submission attempt). This is a UX tradeoff,
   not a compliance one.

2. **Sign a short-lived batch upfront**: when the user has their browser open,
   let them sign any pending/failed records. The signed XML payloads (containing
   no private key) are stored server-side and submitted/retried. The private key
   was never stored — only the already-signed XML is. This is a workable middle
   path.

3. **Keep server-side signing for retries only, browser-side for first attempt**:
   complex dual-path, not worth the added surface.

Option 2 (pre-signed batch queue) is the most pragmatic: the user signs a batch
when online, the server queues and submits, retries use the already-signed XML.
The server never held any key material; it holds signed XML, which is public.

### What "we can't see your private key" actually guarantees — and doesn't

With Option B or C (non-extractable Web Crypto key):
- **Protected against**: server breach (DB dump, env var leak, insider reading
  `CERT_ENCRYPTION_KEY`). The server genuinely has nothing to steal.
- **NOT protected against**: a compromised frontend JS bundle. If we ship
  malicious code (supply chain attack, XSS), it can call `sign()` on arbitrary
  data using the key — even though it can't *export* the key bytes. The
  non-extractable property prevents key exfiltration but not signing abuse.
- **NOT protected against**: browser profile theft (if someone steals the user's
  OS profile, they get the IndexedDB with the `CryptoKey`).

The honest user-facing guarantee: "your private key bytes are never sent to our
servers; we cannot decrypt or export your key." That is a meaningful and true
statement for Options B/C. It cannot be stretched to "your key is safe in
all threat models."

### Spanish regulatory angle

The AEAT Verifactu spec requires a *qualified certificate* for submission
(as defined in eIDAS). It does not mandate *where* the signing computation runs —
only that the signature is valid. Browser-side XAdES-BES produced by `xadesjs`
is structurally identical to server-side `signxml` output; the AEAT would not
know or care.

RGPD: the private key is personal data of a sensitive kind (it authenticates
the user's legal persona). Not storing it server-side removes a RGPD surface
entirely — we'd go from "data processor of user's private key" to "not holding
it at all." This is a simpler position under Articles 25 and 32 (data minimisation,
security by design).

### Feasibility assessment

`xadesjs` + `pkijs` combination is used in production in several EU e-government
portals (Portuguese Autenticação.gov, Latvian e-signatures). The XAdES-BES profile
we need is the most basic profile — well covered. The main implementation risk is
ensuring the `SignedInfo` canonicalization and `X509Data` packaging matches what
the AEAT's SOAP parser expects (this was already validated in T-010 with
server-side `signxml`; the browser-side output must produce the same canonical
form). A focused PoC — sign one `RegistroAlta` in the browser and submit to AEAT
pre-production — would de-risk this in ~1 session.

## Options Considered

- **Option A (Session-only P12 load)** — User picks P12 each session; maximum
  privacy; no key ever stored. Pro: simplest trust story. Con: worst UX;
  impossible to use on mobile without a file picker for P12; breaks any offline
  or background submission pattern.

- **Option B (Non-extractable key in IndexedDB)** — Import P12 once; key stored
  as non-extractable Web Crypto entry in browser storage. Pro: good UX after
  first import; private key bytes never exportable. Con: device/browser-specific;
  clearing site data requires re-import; still vulnerable to signing-abuse via
  XSS.

- **Option C (Hybrid: browser key, server stores cert chain only)** — Cleanest
  model; server holds only the public certificate. Pro: removes the RGPD burden
  of being a private-key data processor; honest "we never had your key" statement;
  cert chain still available for SOAP headers. Con: requires user to re-import key
  on new device; unattended retry needs pre-signed batch queue (Option 2 above).

- **Option D (AutoFirma / native signing client)** — Delegate to Spain's @firma
  ecosystem. Pro: supports hardware tokens; aligned with AEAT's own citizen portal
  approach; no browser crypto complexity. Con: desktop app installation required;
  breaks mobile and web-only users; maintenance dependency on third-party client.

## Open Questions

- Does `xadesjs` produce a `SignedInfo` / `X509Data` structure that the AEAT
  `VerifactuSOAP` parser accepts? (De-risk with a PoC against `prewww1.aeat.es`.)
- For Option B/C: what is the UX for a user who uses multiple devices (laptop +
  phone)? Either we block mobile submission, or we provide a per-device import
  flow, or we accept that mobile users always upload P12 fresh (Option A UX).
- If we adopt the pre-signed batch queue (unattended retry path): does the signed
  XML include a timestamp that could expire before retry? (XAdES-BES does not
  include a trusted timestamp by default — we'd need XAdES-T to embed one. For
  Verifactu the AEAT ignores this field as long as the record's `FechaExpedicion`
  is correct, but needs verification.)
- Does this change the terms of service / data processor agreement we owe users?
  (Likely yes — simpler, better for users. But legal should confirm we're no
  longer acting as a data processor for the private key under RGPD Article 28.)

### Product-manager challenge pass

**Pushback — "sign on browser is inherently safer":**
This claim needs narrowing. Browser-side signing removes the server-breach threat
(the dominant user concern — a DB dump can't steal their key). But it does NOT
protect against XSS or a compromised frontend bundle, which could call `sign()`
on attacker-controlled data. We should not over-sell the guarantee; the honest
framing is "your private key bytes never reach our server" not "your certificate
is fully under your control."

**Pushback — Option D (AutoFirma) as a shortcut:**
Rejected. AutoFirma works well for Spanish citizens filing taxes on the AEAT portal
because those users already have it installed (the AEAT mandated it). FacturaSimple
targets autónomos who need to issue invoices — many will be on managed company
machines or mobile. We cannot assume AutoFirma. Adding an install prerequisite
would be a meaningful drop in activation rate. The web-native Options A/B/C are
the right investigation space.

**Complement — the RGPD simplification is the strongest business argument:**
The submission framing is about user trust ("they can be sure we're not getting
their private keys"). That's a product-marketing claim. The *structural* argument
is stronger: not storing private keys means we are not a data processor for that
data category under RGPD. That eliminates a risk register entry (R-06 is partially
about cert storage), simplifies the RGPD checklist (`docs/rgpd-checklist.md`),
and reduces the compliance surface of AD-3. This should be front-and-centre in
any proposal, not an afterthought.

**Complement — the pre-signed batch queue is underspecified as a UC-002 change:**
If we adopt browser-side signing + pre-signed batch queue, UC-002's alternative
flow 2a ("on failure, queue and retry") needs to be re-specified: the queued item
is now a *signed XML payload*, not an unsigned record + key. The retry worker
never touches key material. This is a meaningful architecture change to AD-3 and
needs a use-case update before delivery.

**Refine — sharpen the PoC question before proposing an iteration:**
The decision-critical unknown is not "is browser-side XAdES possible" (it is,
per ecosystem evidence) but "does `xadesjs` produce a signature the AEAT pre-prod
sandbox accepts." A single-session PoC (one `RegistroAlta` signed in a browser
JS REPL or a minimal HTML test page, submitted to `prewww1.aeat.es`) answers this
definitively. Run that before scoping a full iteration.

Dispositions:
- "sign on browser is safer" — accepted with narrowing: re-framed as "key bytes
  never reach our server" (true and meaningful) not "fully safe" (overstated).
- AutoFirma — rejected: install prerequisite blocks too many users.
- RGPD simplification as primary argument — accepted: promoted to Notes above.
- Pre-signed batch queue UC-002 impact — accepted: added to Open Questions.
- PoC-first before iteration — accepted: reflected in disposition below.

## Where this goes next

→ quick-task — Run a focused PoC: sign one `RegistroAlta` in the browser using
`xadesjs` + `pkijs` and verify acceptance against AEAT pre-production; if the
AEAT accepts it, scope a standard-track iteration to implement Option C (browser
key, server holds cert chain only) with a pre-signed batch queue for unattended
retry.
