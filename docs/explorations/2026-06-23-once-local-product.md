# Exploration: A "ONCE"-style local monolith — does running on the user's own machine dissolve the certificate-custody problem?

**Started:** 2026-06-23
**Question:** If FacturaSimple ships as a single downloadable monolith the user
runs locally (Windows/macOS/Linux), à la 37signals ONCE, does the
certificate-custody problem disappear — and what does that trade away?

## Context

The custody thread so far assumed a **SaaS web app** that holds users' certs:
- [browser-side-signing](2026-06-23-browser-side-signing.md),
  [Q0](2026-06-23-per-record-signing-needed.md),
  [transport-custody](2026-06-23-transport-custody.md),
  [non-verifactu-cert-safety](2026-06-23-non-verifactu-cert-safety.md).

Every one of those wrestled with "how does *our server* avoid holding the user's
private key." The founder now floats a different product shape:
[37signals ONCE](https://37signals.com/podcast/37signals-introduces-once/) — pay
once, own it, install and run it yourself, no subscription, no vendor servers in
the data path. The user's framing is even more local than ONCE's self-hosted
model: **a single monolithic package the user downloads and runs locally on their
own desktop.**

The current product is positioned as an "aplicación web" (presentation doc, AD-3:
"each user supplies their own qualified AEAT certificate, which we store securely
(encrypted at rest)"). A local monolith **contradicts that positioning** — and in
doing so removes the premise of the whole custody thread.

## Notes

### Why local-run dissolves (not solves) the custody problem

If the SIF runs on the user's own machine, **there is no third-party operator to
compromise the cert.** The trust model collapses to "the user trusts their own
computer" — the baseline anyone already lives with. Concretely, every hard
problem from the prior four explorations evaporates:

| Problem (SaaS framing) | Under a local monolith |
|---|---|
| Server holds decryptable P12 + passphrase | **No server.** Cert stays in the user's OS keystore / local file; we never see it. |
| Browser can't drive mTLS to AEAT (JS/CORS) | **Native process** makes the mTLS call directly from the user's machine. No browser limits. |
| Browser can't reach OS keystore / smartcards | **Native** app has full keystore + smartcard/QSCD access (AutoFirma-grade, built in). |
| Unattended event-record signing (non-VERI\*FACTU) | Local app holds the key; can sign events as they occur, no remote session needed. |
| WYSIWYS / malicious-server signs arbitrary records | **No server to serve malicious code.** Residual is binary tampering — a one-time, verifiable install, not a re-served bundle. |
| RGPD: we're a private-key data processor | **We process *no* user data at all** — invoices, clients, cert all stay local. We're not a processor of anything. |

This is the **strongest possible answer to the founder's privacy-first
directive**: not "we can't read your key" but "your key, your invoices, and your
clients never leave your computer." It is also mode-agnostic — it works for
**VERI\*FACTU** (app fires the mTLS submission from the user's machine at
issuance, custody-free) *and* **non-VERI\*FACTU** (local signing + on-demand
remission). The custody problem stops being a reason to prefer one mode.

### The tension ONCE's own products never had: fiscal software goes stale

37signals can sell Campfire/Writebook "buy once, run forever" because **no
regulator changes their spec.** FacturaSimple is the opposite: AEAT changes
formats, schemas, and obligations (the FAQ set was last updated 5 Dec 2025; the
2027 deadlines are staged). A chat app that goes stale is cosmetically dated. A
**Verifactu invoicing app that goes stale produces non-compliant — potentially
illegal — invoices.** "Buy once, run locally forever" and "permanently track a
moving regulatory target" are in direct tension. This is the central risk a naïve
ONCE port would walk into, and it must be designed around, not waved off.

Compounding it: a fleet of heterogeneous local installs is **hard to push urgent
fixes to.** When AEAT ships a breaking schema change with a deadline, a SaaS
operator updates once; a local-monolith vendor must get thousands of users to
re-download in time, or they file bad records.

### The architecture / distribution reality

The current codebase is a **Django web app** (server + SQLite + browser UI). A
local monolith is a different artifact. Rough paths:
- Bundle the existing Django app as a local server + open the system browser at
  `localhost` (PyInstaller / Briefcase / Tauri-sidecar). Reuses most code; the
  "monolith" is a packaged Python runtime + app + SQLite.
- Rewrite as a true native desktop app — large cost, discards current code.

Packaging + code-signing/notarization for **three OSes** (Windows
Authenticode, macOS notarization, Linux packaging) is a real, ongoing eng
surface — modest next to a rewrite, non-trivial next to "ship a Docker image."

### Who is the SIF, and the declaración responsable

Spanish RRSIF makes the **software producer** responsible for a *declaración
responsable* of conformity. That stays **us**, whether SaaS or local — we declare
the software conforms; each user runs their own instance. This does **not** block
the local model, but it means we still carry the certification/conformity
obligation for every version we ship (reinforcing the staleness risk: an outdated
local install is a version *we declared conformant* now drifting out of spec).

### What this does to the prior explorations

- **browser-side-signing** — *obviated.* Native local signing is strictly
  stronger (full keystore/smartcard access, no CORS/JS-mTLS limits, no
  malicious-server WYSIWYS gap). Browser crypto was only ever a workaround for
  *not* being on the user's machine.
- **transport-custody** — *dissolved.* mTLS runs from the user's machine with the
  user's own cert; no third-party custody exists to remove.
- **Q0 (per-record-signing)** — *still relevant* for *which records need signing*
  per mode, but its custody implication is moot.
- **non-verifactu-cert-safety** — the "whose cert signs / browser vs server"
  machinery becomes moot for custody; locally you simply use the user's own cert
  natively. The *declaración responsable / SIF identity* question survives; the
  custody question does not.

The local monolith is a candidate **dominant solution** to the custody thread —
at the price of a business-model + architecture pivot and the compliance-currency
risk above.

## Options Considered

- **Option 1 — Local desktop monolith, pure ONCE (buy once, no recurring
  relationship).** Pro: maximal privacy (no user data ever leaves the machine);
  custody problem gone; aligns with founder directive; offline-capable; no SaaS
  security/ops surface. Con: **compliance-staleness risk is severe for fiscal
  software**; no funded mechanism for the regulatory update treadmill; urgent-fix
  propagation across thousands of installs; 3-OS packaging; loses recurring
  revenue that the permanent update obligation arguably *requires*.
- **Option 2 — Local monolith + paid "regulatory currency" update plan (hybrid).**
  Sell the app once (you own it, runs locally, custody-free) but updates for AEAT
  changes are a separate, optional-but-strongly-advised maintenance subscription.
  Pro: keeps the local-custody win *and* funds the compliance treadmill; honest
  about why fiscal software differs from Campfire. Con: not "pure" ONCE; users who
  lapse run stale/non-compliant software (support + liability question); two
  things to build (app + update channel).
- **Option 3 — Self-hosted server (ONCE-as-published, for pymes).** Install on a
  box the customer controls (their own server/NAS), multi-user. Pro: same
  custody-free property; fits multi-seat pymes better than a desktop app. Con:
  "run a server" excludes the solo-autónomo segment FacturaSimple targets; more
  user-side ops.
- **Option 4 — Stay SaaS (status quo); address custody via the prior
  explorations.** Pro: keeps current architecture, recurring revenue, central
  update control (compliance currency is *easy*); the staleness risk is ours to
  manage centrally. Con: the custody problem remains real and only partially
  solvable (transport-custody / non-verifactu notes); we remain a data processor.

## Open Questions

- **[product/business, decision-critical] Is the founder willing to trade the SaaS
  model (recurring revenue, central compliance updates) for a local product whose
  privacy story is unbeatable but whose update/liability model is unsolved?** This
  is a vision-level pivot, not a feature.
- **[product] How is regulatory currency funded and enforced in a local model?**
  Forced-update? Expiry/"this version conformant until DATE"? Paid maintenance
  plan (Option 2)? Without an answer, Option 1 ships a liability.
- **[legal] Does a stale local install that files a non-conforming record expose
  *us* (the declaring software producer) or only the user?** Shapes how hard the
  update mechanism must be.
- **[legal] Does the declaración responsable / SIF-producer obligation impose
  anything that a distributed local-install model can't satisfy** (e.g. ability to
  attest each running version)?
- **[eng] Packaging path** — bundle Django-as-localhost (cheap, reuses code) vs.
  native rewrite (expensive)? And the 3-OS code-signing/notarization pipeline.
- **[product] Segment fit** — desktop monolith (solo autónomo) vs self-hosted
  server (pyme). One product or two?

### Product-manager challenge pass

(role hat: `.claude/teammates/product-manager.md` — no team deployed)

- **Pushback — the custody win is real but it's not the dimension the business
  lives or dies on; compliance-currency is.** A solo autónomo's dominant need is
  "issue a *legally correct* invoice in <5 min," and *correct* is a moving target
  AEAT controls. A local monolith makes the privacy story unbeatable while making
  the *correctness-over-time* story **worse** — the opposite of the core value
  prop. Adopting ONCE to win custody, at the cost of the thing users actually
  depend on, would be a bad trade unless Option 2's update mechanism is part of
  the plan from day one. Accepted: staleness named as the central con; Option 2
  promoted as the only responsible form of the local model.
- **Pushback — ONCE's economics assume a static spec; ours isn't static.**
  37signals' "no recurring revenue" works because there's no treadmill to fund.
  Fiscal software *has* a permanent treadmill. Pure buy-once (Option 1) structurally
  underfunds the one obligation the product can't skip. Accepted: pure Option 1
  flagged as economically mismatched to the domain; hybrid (2) or SaaS (4) are the
  economically coherent ends.
- **Complement — the local model maximises the RGPD argument that has been the
  strongest business case throughout.** Across all four prior explorations the
  durable business win was data-minimisation (not being a processor). Local-run
  takes that to its limit: **we process no user data at all.** That is a genuine,
  marketable differentiator ("your books never leave your computer") *if* the
  staleness problem is solved. Accepted: this is the strongest pro and should lead
  any pitch of the local model.
- **Refine — the decision is business-model-first, technical-second.** The
  packaging questions (PyInstaller vs rewrite) are downstream of a founder call on
  SaaS-vs-ONCE-vs-hybrid and on how compliance currency is funded. Don't scope eng
  until that call is made. Accepted: disposition is a founder decision brief, not
  an implementation iteration.
- Disposition per challenge: all accepted into notes/options; none rejected. Net
  steer: the local monolith is the **cleanest answer to custody and the strongest
  privacy/RGPD story**, but **pure ONCE is mismatched to fiscal software's update
  treadmill** — only a hybrid (local app + funded regulatory-currency channel,
  Option 2) is responsible. The choice between that and staying SaaS (Option 4) is
  a vision-level call only the founder can make, and it **supersedes the
  custody-engineering of the prior four explorations** (which all presume SaaS).

## Where this goes next

→ iteration — **Founder decided the model (see below); promote to a vision +
architecture pivot.** The decision brief is superseded by a direct founder call.

## 2026-06-23 — Founder decision: ship the local ONCE model

The founder resolved both decision-critical questions directly:

1. **Model: ONCE-style local monolith — confirmed.** The staleness risk is
   handled by **honest disclaimer/versioning**, not a forced-update mechanism:
   the product states **"cumple con la normativa Veri\*FACTU vigente"** (compliant
   with *current* Verifactu) as of its release. Simple value proposition, clear
   tradeoff stated up front. This selects **Option 1 (pure local ONCE)** as the
   day-one shape.
2. **Regulatory currency: defer, don't pre-build.** Verifactu is not expected to
   change often (the government does not revise frequently); we are explicit about
   "current" in the disclaimer, and **an upgrade plan for existing customers is a
   *later* offering**, not a launch requirement. Option 2's paid update channel is
   thus a **future** evolution of Option 1, not a prerequisite.

### Corollary the decision forces: local-run makes VERI\*FACTU the clear mode

The only reason non-VERI\*FACTU was ever attractive
([non-verifactu-cert-safety](2026-06-23-non-verifactu-cert-safety.md)) was to turn
the cert into a *local signing key* and keep it off our server. **Local-run
removes the cert from our server in *both* modes** — so that rationale is gone.
With custody no longer the deciding factor, the modes sort purely by burden, and
**VERI\*FACTU wins decisively**: lighter compliance surface (no event log, no
alarm management, no signature-verification/export machinery, no per-record XAdES
obligation), and it is fully custody-free locally because the mTLS submission
fires **from the user's own machine** with the user's own cert. Net shape:

> **Local monolith (Win/macOS/Linux) + VERI\*FACTU mode + "compliant with current
> Verifactu" disclaimer + the user's cert held only on their own machine.**

### What this closes

- **transport-custody, browser-side-signing** — *moot.* No server in the data
  path; native local mTLS + native local signing where needed.
- **non-verifactu-cert-safety** — *not pursued.* Local-run + VERI\*FACTU is
  lighter and equally custody-free; the heavier non-verifiable path buys nothing
  here.
- **Q0 (per-record-signing)** — its finding stands (VERI\*FACTU submits no
  per-record signature); `compliance/signing.py` remains unwired groundwork.

### Delivery path (spec-first, per CLAUDE.md — behaviour/architecture change)

This is a vision-level pivot; the spec must change before code. In order:
1. **Vision** (`/openup-create-vision`) — reposition from "aplicación web" to a
   locally-run, user-owned product; state the Verifactu-vigente disclaimer and the
   "your data never leaves your computer" privacy claim as the headline.
2. **Architecture** (`/openup-create-architecture-notebook`) — supersede **AD-3**
   (server-stored encrypted cert) with a local-custody decision; record the ONCE
   packaging decision (Django-as-localhost bundle vs. native — own AD); note mTLS
   now originates client-side.
3. **Roadmap re-plan** (product-manager ordering) — packaging/distribution + 3-OS
   code-signing become first-class work items; the SaaS cert-storage/encryption
   surface (`certificates/crypto.py` server custody) is reframed or retired.

This is multi-role (architect + analyst + PM) and architectural → **full track**.

### 2026-06-23 — v1 packaging decision (founder)

Two constraints set the packaging direction:
- **Binary size ≤ ~150MB** → disqualifies bundling a browser engine. **Electron
  is out** (Chromium ~120–150MB before the Python payload). Viable: system-browser
  (PyInstaller) or system-WebView (Tauri) — both omit Chromium and fit after
  pruning.
- **OS-keystore mTLS desirable** (Windows CertStore / macOS Keychain / PKCS#11
  smartcard, DNIe) — but **client-cert TLS from an OS store is painful in pure
  Python** (stdlib `ssl`/OpenSSL won't use non-exportable store keys; current
  `requests_pkcs12` is P12-bytes-only). Doing it well wants a **native (Rust)
  transport layer**.

**Decision: keystore is a *later* enhancement, not v1.** v1 ships:

> **PyInstaller Django-as-localhost + system browser + the current P12-upload
> flow (`requests_pkcs12`).** Smallest, simplest, maximal reuse of `compliance/` +
> `invoicing/` + `submission/`. Native keystore/PKCS#11 transport (smartcard/DNIe)
> is a **follow-on AD**, likely a small Rust/native transport helper.

**De-risking spike (before locking the packaging AD):** measure the pruned
PyInstaller Django artifact size on all three OSes against the 150MB budget. (The
keystore-mTLS feasibility probe is deferred with the feature.)
