# Exploration: Submitting to AEAT without server-held private-key custody (mTLS transport)

**Started:** 2026-06-23
**Question:** Can VERI\*FACTU submission to AEAT be performed without our server
holding *decryptable* private-key material for the mutual-TLS handshake?

## Context

This supersedes the shelved dual-track scope of
[2026-06-23-browser-side-signing.md](2026-06-23-browser-side-signing.md) for the
current flow. The Q0 finding
([2026-06-23-per-record-signing-needed.md](2026-06-23-per-record-signing-needed.md))
established that the user certificate's **only load-bearing role** in the live
VERI\*FACTU flow is **mTLS client authentication** in
`submission/aeat_direct.py::_default_transport()` — *not* the per-record XAdES
signature (which production never generates and never submits). The
[legal finding](2026-06-23-legal-qscd-finding.md) confirms Verifactu mode needs
no per-record signature at all.

So the founder's directive — "never store the private key/passphrase
server-side" — does **not** bite on signing. It bites on the **transport layer**.
This file scopes that real problem.

## Notes

### What the server holds today, exactly

- `certificates/crypto.py` — AES-256-GCM envelope encryption; the server holds
  `CERT_ENCRYPTION_KEY` (the *only* holder) and the ciphertext.
- `certificates/services.py::store_certificate()` encrypts **both** the P12 bytes
  **and** the passphrase at rest. `get_cert_material()` decrypts **both** to
  plaintext on every submission — "the sole sanctioned plaintext path."
- `submission/aeat_direct.py::_default_transport()` mounts that plaintext P12 as
  a TLS client cert (`Pkcs12Adapter`) and POSTs the SOAP body to AEAT.

**The exposed surface:** the server can decrypt the user's full P12 + passphrase
at any moment (it has key + ciphertext). A DB dump alone is insufficient (it's
encrypted), but DB dump **+** `CERT_ENCRYPTION_KEY` (env leak, insider, memory
scrape) yields the user's qualified-certificate private key in the clear. That is
the surface to remove.

### Why the browser cannot take this over (settled, not re-litigated here)

mTLS client-cert selection happens in the browser/OS TLS stack during the
handshake and is **not exposed to JavaScript** (`fetch` can't supply an uploaded
P12 as the client cert); and same-origin/CORS blocks a browser page from POSTing
to `*.aeat.es` regardless. The mTLS call must originate from a non-browser
process — a server we control, or software on the user's machine. That fork is
the whole decision.

### The core trade-off

Removing server custody means the mTLS call must run **on the user's machine**
(native client / local proxy), OR custody must be reduced to **in-memory-only,
never-decryptable-at-rest** server-side. Each buys a different slice of the threat
model at a different UX/eng cost. The honest framing: there is no
"browser-only, no install, no server custody" point in the design space — the
transport constraint forecloses it.

### Threats, and which option addresses which

| Threat | Current | A: native | B: local proxy | C: ephemeral mem | D: keep custody |
|---|---|---|---|---|---|
| DB dump + key leak → key stolen | ✗ exposed | ✓ removed | ✓ removed | ~ only during a live submit | ✗ exposed |
| Malicious server abuses key (signs/submits) | ✗ | ✓ (user-present) | ~ (proxy policy) | ✗ (server drives it) | ✗ |
| Hardware-token / QSCD support | ✗ | ✓ | ~ | ✗ | ✗ |
| Works on mobile / no install | ✓ | ✗ | ✗ | ✓ | ✓ |
| Unattended retry possible | ✓ | ✗ | ✗ | ✗ | ✓ |

"~" = partial / depends on design. Note C only narrows the *at-rest* window; a
breached **running** server still sees plaintext during a submission, so C does
**not** defend against a malicious server — it defends against cold-storage
theft.

## Options Considered

- **Option A — Native/desktop client makes the mTLS call from the user's
  machine** (AutoFirma-style, or our own thin agent). The cert lives in the OS
  keystore / smartcard / local P12; the user's machine POSTs to AEAT directly (or
  signs a transport challenge); our server only stores records + outcomes. Pro:
  server never holds key material at all — strongest custody removal; supports
  hardware tokens (highest assurance). Con: install prerequisite; **blocks mobile
  / web-only users**; no unattended retry; we own a desktop-agent maintenance
  surface (or depend on AutoFirma's `@firma` ecosystem).

- **Option B — Trusted local proxy on the user's machine** terminates mTLS to
  AEAT; our backend hands it the SOAP body, it attaches the client cert locally.
  Pro: key stays on the user's machine; thinner than a full native signing app.
  Con: still an install; a local HTTP endpoint is its own security surface; same
  mobile/unattended limits as A; arguably A with extra moving parts.

- **Option C — Ephemeral in-memory-only server custody.** The user supplies the
  P12 + passphrase per submission session (or per submit); the server uses it for
  the mTLS handshake **in memory only** and never persists it decryptably —
  `store_certificate` stops writing the encrypted blob; `get_cert_material` is fed
  from a transient request, not the DB. Pro: removes the *at-rest* surface (no DB
  dump + key leak path); keeps mobile/web reach; no install. Con: does **not**
  defend against a *running* breached server (it sees plaintext during submit);
  **breaks unattended retry** (no stored cert to retry with); worse UX (cert
  re-supplied each session). This is the only "web-native" custody reduction, but
  it's a partial one — honesty required in any user-facing claim.

- **Option D — Accept server custody, harden it.** Keep the current model; invest
  in key-management hardening instead (KMS/HSM-backed `CERT_ENCRYPTION_KEY`,
  envelope re-keying, strict access logging, short-lived in-process decryption).
  Pro: zero UX/reach cost; keeps unattended retry; meaningfully raises the bar on
  the env-leak/insider path. Con: does **not** satisfy the literal "never store
  the private key server-side" directive — the server *can* still decrypt.

## Open Questions

- **Does AEAT support any auth mode other than mTLS client cert** for the
  VERI\*FACTU webservice (e.g. a signed-request scheme that could be produced on
  the user's machine and relayed)? If the *only* accepted auth is the TLS
  handshake itself, then the call genuinely must originate where the key is, and
  Option C's server-side handshake is unavoidable for web users. **Decision-
  critical** — gates whether a "user-machine signs, our server relays" hybrid even
  exists.
- **How material is the at-rest-only threat reduction (C) vs. its costs?** If the
  realistic threat is cold DB theft (not a live-server compromise), C buys most of
  the value cheaply; if it's a running-server compromise, C buys little and only
  A/B help.
- **Does the founder's directive mean "never decryptable at rest" (C suffices) or
  "server never sees plaintext, ever" (only A/B suffice)?** The two readings pick
  different options. Needs the founder, not us.
- **Unattended retry** (currently relied on by UC-002 alt-flow 2a): A/B/C all
  break it. Is dropping it acceptable (re-surface failures in UI), as the
  browser-signing revision already proposed?
- Hardware-token / QSCD demand among the target autónomo segment — real, or a
  security-purist preference? Drives whether A's smartcard support earns its cost.

### Product-manager challenge pass

(role hat: `.claude/teammates/product-manager.md` — no team deployed)

- **Pushback — is this founder-directive-driven or user-value-driven?** The
  directive is "never store the private key server-side," but no target-user pain
  has been cited — autónomos asking us to issue invoices have not (yet, on
  record) said cold-storage key custody blocks adoption. The strongest *business*
  case remains the one from the parent exploration: **not being a private-key data
  processor under RGPD Art. 28** trims R-06 and `rgpd-checklist.md`. That is real
  and survives here — but it is satisfied by removing *at-rest* custody (Option C),
  which is far cheaper than a desktop agent (A/B). Accepted: C is the value-
  proportionate default unless the founder's directive explicitly means "never see
  plaintext," in which case A. Flagged to founder as the gating question.

- **Pushback — Option A/B blocks the core segment.** FacturaSimple's pitch (per
  the presentation doc) is "issue a correct invoice in <5 minutes, no technical
  knowledge, web-native." An install prerequisite and the loss of mobile directly
  contradict that positioning and would depress activation. A/B should not be the
  *default* path for the mass segment; at most an **opt-in high-assurance arm**.
  Accepted: if pursued, A is a second track, not the primary — mirroring the
  (now-shelved) dual-track instinct, but correctly aimed at transport this time.

- **Complement — the directive may be cheaper to honour than it looks.** If AEAT
  accepts only mTLS, "never store at rest" (C) is achievable with **no install**
  by re-supplying the cert per session. The eng change is mostly *subtractive*
  (stop persisting the encrypted blob; feed `get_cert_material` from the request),
  which is unusually low-cost for a security win. Worth pricing before assuming
  the desktop-agent road. Accepted: C costed first.

- **Refine — the decision-critical unknown is AEAT's accepted auth modes, not our
  client architecture.** Just as Q0 found the real question was "is signing even
  submitted," the real question here is "does AEAT accept anything other than a
  live mTLS handshake." Resolve that *before* scoping A/B/C — it can eliminate
  whole options. Accepted: it leads "Where this goes next."

- Disposition per challenge: all accepted into the notes/options above; none
  rejected. Net steer: price Option C (at-rest removal, web-native) as the value-
  proportionate path; treat A as an opt-in high-assurance second track; gate
  everything on the AEAT-auth-modes probe and the founder's directive reading.

## Where this goes next

→ quick-task — **De-risk the gating unknown first:** a focused probe of AEAT's
VERI\*FACTU webservice authentication options (is live mTLS the only accepted
mode, or is there a relayable signed-request path?) plus one founder question —
does "never store the private key server-side" mean *never decryptable at rest*
(Option C suffices) or *server never sees plaintext* (Option A/B required)? Those
two answers collapse the option set; only then promote the surviving option to a
standard-track iteration. Do **not** scope an implementation iteration before both
are answered.
