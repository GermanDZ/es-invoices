# Exploration: Can we be compliant in non-VERI\*FACTU mode without compromising the user's certificate?

**Started:** 2026-06-23
**Question:** In non-VERI\*FACTU mode the certificate is a *local XAdES signing
key* (it never contacts AEAT at issuance), not a transport key — does that let us
be fully compliant without our server ever holding the user's private key?

## Context

This is the synthesis turn over three prior notes:
- [browser-side-signing](2026-06-23-browser-side-signing.md) — XAdES signing
  *can* run in the browser (Web Crypto + `xadesjs`/`pkijs`); software P12 is
  legally sufficient (no QSCD).
- [per-record-signing-needed (Q0)](2026-06-23-per-record-signing-needed.md) — in
  **VERI\*FACTU** mode our code submits *no* signature; the cert is used only for
  mTLS, every issuance.
- [transport-custody](2026-06-23-transport-custody.md) — in VERI\*FACTU the cert
  is a transport key the browser can't drive; custody is hard to remove.

The founder's input reframes the fork: **switch the product to non-VERI\*FACTU**,
where the cert's job is to *sign* records locally (XAdES Enveloped, per the AEAT
`firma` FAQ), not to authenticate a per-issuance call to AEAT. Signing is local
computation → browser-doable → the key need never reach our server. The
[legal finding](2026-06-23-legal-qscd-finding.md) already cleared software P12
signing.

## Notes

### Why non-VERI\*FACTU flips the custody story in our favour

| | VERI\*FACTU | non-VERI\*FACTU |
|---|---|---|
| Cert's role | mTLS transport key | **XAdES signing key** |
| Fired when | **every issuance** | every issuance (signing) + rare remission |
| Contacts AEAT at issuance | yes | **no** |
| Browser can do it | no (mTLS not JS-exposed) | **yes (signing is local)** |
| Compliance burden | lighter | **heavier** (event log, alarms, export, verification, multi-year custody) |

In VERI\*FACTU the load-bearing cert operation (mTLS) is exactly the one a
browser can't perform → custody stuck on the server. In non-VERI\*FACTU the
load-bearing cert operation (XAdES signing) is exactly the one a browser *can*
perform → **the original browser-side-signing exploration becomes load-bearing
and correct here**, where it was a no-op for VERI\*FACTU.

So the headline: **yes, cert-safety is achievable — but only in the more
burdensome compliance mode.** You buy "we never hold the user's key" with event
logging, alarm handling, signature verification, export, and local multi-year
custody. That is a real product-scope trade, not a free win.

### Three catches that stop this being clean

**Catch 1 — Art. 8.1 remission capability still requires the mTLS/SOAP code to
exist.** The `capacidad-remision` FAQ (RRSIF art. 8.1) requires *every* SIF —
non-VERI\*FACTU included — to be able to remit records to AEAT "de forma
continuada, segura, automática e instantánea," e.g. on a *requerimiento* or to
switch to VERI\*FACTU at any time. So we don't delete the mTLS transport; we just
**don't fire it at issuance**. The transport-custody question doesn't vanish — it
becomes *rare and user-attended* (responding to a requerimiento / opting into
VERI\*FACTU). That is the key UX difference: an ephemeral/just-in-time cert supply
(Option C from transport-custody) is perfectly acceptable for a once-in-a-while
attended remission, where it was poor UX for every issuance. **Catch 1 is
survivable** and actually makes the cheap custody option viable.

**Catch 2 — unattended event-record signing.** The `firma` FAQ says
non-verifiable systems must XAdES-sign **all record types they generate —
facturación (alta/anulación) *and* event records.** Some event records are
generated with **no user present**: anomaly/integrity-failure detection, backup
restoration, end-of-NO-VERI\*FACTU-operation, period summary events. If signing
is browser-only, **these cannot be signed when they occur** — the same
unattended-operation hole the browser-signing revision hit, now for the event
log. This is a genuine blocker for a pure browser-only-key model, unless event
records are signed by a *different* signer (see Catch 3).

**Catch 3 — the dominant unknown: WHOSE certificate signs?** Everything above
assumes the signer is the *user's* (obligado's) qualified cert. But a SaaS SIF
may be entitled to sign records with the **SIF's own certificate** (a *sello* of
the software producer / the system), not each user's personal cert. If so:
- The user's personal qualified cert is **never used for signing at all** → the
  "compromise the user's cert" problem **dissolves entirely**.
- Our server signs with **our own** sello (a credential we legitimately custody —
  not a user-custody problem), which also **solves Catch 2** (unattended event
  signing uses our sello).
- The user's cert, if needed at all, is only for *remission authentication* under
  Catch 1 — rare, attended, ephemeral-supply-able.

This single regulatory fact reorders the entire solution space. **It is the
decision-critical unknown and must be answered before any option is scoped.**

### What "compliant without compromising the cert" actually requires

Depending on Catch 3's answer, the compliant cert-safe architecture is one of:

- **If SIF may sign with its own sello (best case):** server signs all records +
  events with FacturaSimple's sello; user never supplies a signing cert; user's
  cert only appears (if at all) for attended on-demand remission. No user-key
  custody anywhere. Cleanest — but introduces a "we sign on behalf of users"
  legal/contractual posture to validate.
- **If the obligado's own cert must sign:** browser-side XAdES for
  facturación records (key never reaches server) + an answer for unattended event
  signing (Catch 2) — likely a degraded/queued path or accepting that event
  signing requires a user session. Plus attended remission (Catch 1). Harder,
  and the WYSIWYS caveat from the browser-signing revision applies (a breached
  server could hand the browser a malicious record to sign).

### Honest guarantee, restated

Even in the best case, "we never hold your key" defends key *exfiltration*, not
*signing abuse* by a breached server that controls *what* the browser signs
(WYSIWYS gap) — unless the SIF-sello model removes the user's signing cert from
the picture, in which case the user-key threat genuinely goes to zero (the
residual is then *our* sello's custody, which is our problem to harden, not the
user's exposure).

## Options Considered

- **Option 1 — Non-VERI\*FACTU + SIF-sello signing (server signs with our own
  cert).** Pro: user's personal cert never used for signing → user-key-compromise
  problem dissolves; solves unattended event signing; web-native, mobile-friendly.
  Con: depends on Catch 3 being legally true; we become signer-on-behalf (ToS /
  apoderamiento questions); we take on the full non-VERI\*FACTU burden (event log,
  alarms, export, verification, custody); our sello becomes a high-value custody
  asset to harden.
- **Option 2 — Non-VERI\*FACTU + browser-side signing with the obligado's cert.**
  Pro: honest "your key never reaches our server" for facturación records; software
  P12 legally fine. Con: unattended event signing unsolved (Catch 2); WYSIWYS gap;
  multi-device UX; still owes the full non-VERI\*FACTU compliance machinery.
- **Option 3 — Stay VERI\*FACTU, accept transport custody (status quo + harden).**
  Pro: far lighter compliance burden; unattended retry intact; the
  transport-custody exploration's Option D. Con: server can decrypt the user's
  cert; does not satisfy "never compromise the user's cert."
- **Option 4 — Stay VERI\*FACTU, ephemeral transport custody.** Pro: removes
  at-rest key storage; light compliance burden. Con: per-issuance cert re-supply
  is poor UX; only narrows the at-rest window, not running-server breach
  (transport-custody Option C).

## Open Questions

- **[legal, decision-critical] Whose certificate signs the records — the
  obligado's qualified cert, or may the SIF sign with its own *sello*?** Answer
  selects Option 1 vs 2 and determines whether the user-key problem exists at all.
  Sources to mine: `firma.html` FAQ + RRSIF / Orden HAC/1177/2024 on the signing
  certificate's holder; the firma-vs-sello point already noted in the legal
  finding.
- **[legal] On-demand remission (Art. 8.1): must it be the automated mTLS
  webservice, or does a manual sede-electrónica export/upload (AutoFirma/Cl@ve)
  satisfy "automática e instantánea"?** If manual suffices, we may not need
  server-side mTLS at all → cert never needed for transport either.
- **[legal] Does signing-on-behalf (Option 1) require apoderamiento / colaboración
  social registration, and does that change our RGPD processor posture?**
- **[product] Is the non-VERI\*FACTU compliance burden (event log, alarm
  management, signature verification, export, multi-year local custody) worth the
  cert-safety win, vs. VERI\*FACTU + transport hardening?** This is the real
  strategic call.
- **[design] If event records must be obligado-signed and can occur unattended
  (Catch 2), what is the fallback** — queue until next session, degrade, or is it
  fatal to Option 2?

### Product-manager challenge pass

(role hat: `.claude/teammates/product-manager.md` — no team deployed)

- **Pushback — "non-VERI\*FACTU protects the cert" is true but sold without its
  price tag.** The cert-safety win is real, but it is bought with *strictly more*
  compliance surface (the AEAT FAQ is explicit non-verifiable is the heavier
  path). For a product whose pitch is "issue a correct invoice in <5 min, no
  technical knowledge," taking on event logging + alarm management + export +
  verification + multi-year custody is a **major scope and positioning shift**,
  not a security tweak. The value case must clear that bar, not just the cert one.
  Accepted: burden named as a first-class con on Options 1 & 2; flagged as the
  strategic call.
- **Pushback — is cert-safety a stated user need or a founder-aesthetic?** No
  target autónomo has (on record) refused FacturaSimple over cold-storage key
  custody. The durable *business* argument remains RGPD data-minimisation (not
  being a private-key processor, Art. 28) — and **Option 1 (SIF-sello) delivers
  that more cleanly than any browser scheme**, because the user supplies no key at
  all. Accepted: this strengthens Option 1 over Option 2 on the business axis,
  independent of the security framing.
- **Complement — the "whose cert" question dwarfs every technical option.** The
  prior three explorations all reasoned about the *user's* cert; none asked
  whether the SIF signs with its *own*. If it may, the entire problem these notes
  chase **ceases to exist** for signing. That one legal fact should be answered
  before a single line of signing/transport architecture is scoped. Accepted:
  promoted to the lead open question and the disposition.
- **Refine — the question to put to legal is not "is browser signing possible"
  (settled: yes) but "who is the lawful signer and does on-demand remission need
  the webservice."** Two cheap legal answers collapse a four-option space to one.
  Accepted: disposition is a legal probe, not an implementation iteration.
- Disposition per challenge: all accepted into notes/options; none rejected. Net
  steer: do **not** scope signing or transport implementation yet; the
  cert-safety win is real but mode-burden-laden, and which architecture even
  applies hinges on two unanswered legal questions (whose cert signs; remission
  modality). Option 1 (SIF-sello) is the most promising *if* legally available —
  it dissolves the user-key problem and best serves the RGPD argument.

## Where this goes next

→ quick-task — **A focused legal/regulatory probe answering two questions before
any architecture is scoped:** (1) may a SaaS SIF sign facturación + event records
with its *own* certificate/sello, or must the obligado's qualified cert sign? and
(2) does Art. 8.1 on-demand remission require the automated mTLS webservice, or
does manual sede-electrónica export/upload satisfy it? Mine the AEAT `firma` and
`capacidad-remision` FAQs + Orden HAC/1177/2024, reusing the legal-finding doc.
Those two answers select between Option 1 (SIF-sello — likely cleanest, user-key
problem dissolves) and Option 2 (browser-side obligado signing), and determine
whether server-side mTLS is needed at all — only then promote the survivor to a
standard-track iteration that also prices the non-VERI\*FACTU compliance burden.
