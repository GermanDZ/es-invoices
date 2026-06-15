# T-007 — AEAT/Verifactu Submission Spike: Findings & Build-vs-Buy Analysis

> Time-boxed Elaboration spike (R-03, the highest live technical exposure).
> Resolves the open seam **AD-3** (AEAT submission adapter) in the architecture
> notebook. Output: a documented feasibility assessment + a build-vs-buy
> recommendation for founder ratification. Traces from UC-002, R-03, AD-3, Q-2.

## 1. What "submission" actually is (target system)

FacturaSimple is **Verifactu-native** (Vision §2). The relevant system is the
AEAT **VERI\*FACTU** regime under the *Reglamento de los sistemas informáticos de
facturación* (RD 1007/2023, RRSIF) and the technical/functional spec
**Orden HAC/1177/2024** (antifraud Ley 11/2021 lineage).

A *Sistema Informático de Facturación* (SIF) can operate in two modes:

- **VERI\*FACTU (sending) mode** — each billing record (`registro de facturación
  de alta` / `de anulación`) is transmitted to the AEAT right after issuance via
  an AEAT **web service**. Records are **hash-chained** (each carries the `huella`
  of the prior record). Because the AEAT holds the records, on-device anti-tamper
  requirements are lighter.
- **No-VERI\*FACTU mode** — records are *not* routinely sent; they are stored
  locally under a qualified e-signature with stricter integrity/conservation
  duties, producible on AEAT request.

FacturaSimple commits to **sending mode** → it must speak to the AEAT submission
web service. That endpoint is the entirety of what AD-3's adapter wraps.

**Transport shape (to validate in the sandbox):** an AEAT **SOAP web service**;
request/response are **XML against published XSD schemas**; authentication is by
**qualified electronic certificate** (client-cert TLS). The response reports a
per-record outcome — `Correcto` / `AceptadoConErrores` / `Incorrecto` — with
AEAT error codes. A **preproducción (sandbox)** environment exists for testing.

**Adjacent systems explicitly NOT in this scope (avoid conflation):**
- **TicketBAI** — the *territorios forales* (País Vasco / Navarra) regime, a
  *different* system. Verifactu is the **común-territory** AEAT regime. v1 is
  común-territory only (consistent with N-6 Spain-only); foral support is a
  separate decision (see Open Question O-3).
- **Facturae / FACe** — B2G (public-administration) e-invoicing. Different track.
- **B2B mandatory e-invoicing** (Ley *Crea y Crece*) — still pending its
  implementing regulation as of this spike; not Verifactu, not v1.

## 2. Feasibility (does the BUILD path actually work?)

Verdict: **feasible, medium effort, and de-riskable inside a time box.**

- The **WSDL + XSD schemas + technical docs are public** (AEAT publishes them),
  so the contract is knowable up front.
- Our chosen stack (AD-5 **Python + Django**) has mature tooling for every piece:
  `zeep` (SOAP client), `signxml` (XAdES/XML-DSig — already cited in AD-5),
  `lxml`/`cryptography` (XML + cert/TLS), and the standard library for the
  `huella` hash-chain.
- Critically, **record generation + hashing + signing is already CORE and
  in-house** (AD-2: the versioned compliance/Verifactu module). The marginal work
  for direct submission is therefore *the SOAP call + auth + response handling* —
  an incremental transport layer, **not** a new subsystem.

**The three things a build PoC must actually prove in `preproducción`:**
1. **Certificate auth** against the AEAT web service (the fiddliest government-
   integration friction — R-03's named trigger).
2. **Exact XML/XSD conformance** of an `alta` record → an `AceptadoConErrores`
   or `Correcto` response.
3. **`huella` hash-chain** computed per spec and accepted across two chained
   records (alta then a second alta / anulación).

If these three clear inside the time box, R-03 collapses from "high" to "managed."

## 3. Build vs Buy

The only outsourceable seam is the **submission transport** — because AD-2
already keeps record generation + hashing + signing in-house as CORE. So "buy"
means buying a thin transport (or ceding part of the core, which contradicts
AD-2).

| Criterion (source) | Leans | Why |
|---|---|---|
| **R-04** price-sensitive market / thin margins | **BUILD** | A gateway's **per-document fee** is a direct COGS hit on *every* invoice — hard to sustain at low price points. Build has no recurring per-doc cost. |
| **Q-3 / R-06** EU residency, RGPD | **BUILD** | A gateway is an added **sub-processor** to vet + a DPA to sign; build keeps data inside our own EU stack (AD-4). |
| **AD-2 + R-01** compliance is core, isolated, spec-change-absorbing | **BUILD** | Build owns the whole compliance path coherently in one versioned module; a gateway **splits** compliance ownership. |
| **R-03** integration is the highest risk | **BUY** | The one real argument for buying: a provider **owns AEAT comms + tracks spec changes**, offloading the fiddly government integration. |
| **Q-6** lean / favor build-vs-buy for non-core | **mixed** | Favors buy for non-core — but submission sits *adjacent to* the core compliance module, and the transport is thin. |
| **Q-2** submission reliability ≥99% | **mixed** | A provider SLA can help; but it also inserts a **third-party dependency in the critical path** (their outage = our users can't report). |

**Net:** the criteria lean **BUILD**, with **R-03 (risk)** the sole strong pull
toward BUY. The decisive asymmetry: record generation + signing is in-house
*regardless* (AD-2), so buying a gateway means **paying a recurring per-invoice
fee for a thin SOAP call we are 80%-equipped to make** — unless the build PoC
fails, in which case buying the risk away is worth it.

### Gateway providers (candidates — pricing / current Verifactu support / EU residency MUST be validated, not assumed)

Verifacti, B2Brouter, EDICOM, Docuten, SERES, Voxel — Spanish-market e-invoice /
SIF gateways that expose a REST API (POST record → they sign + submit + return
status). *Named from domain knowledge; none verified for current Verifactu
coverage or price here — that diligence is part of the BUY branch if taken.*

## 4. Recommendation (for founder ratification)

**Recommend: BUILD direct integration as the v1 target — gated by a sandbox
PoC — and keep AD-3's interface so a gateway adapter can be swapped in if the
PoC blows its time box.** Concretely:

1. Attempt the **build PoC** against `preproducción` (the three proofs in §2).
2. **PoC clears the time box → BUILD** is the AD-3 adapter for v1.
3. **PoC exceeds the time box / cert or conformance blocks persist → BUY** a
   gateway adapter behind the *same* AD-3 interface (this is exactly R-03's
   pre-agreed mitigation; no architecture rework).

This keeps cost out of every invoice (R-04), data in our EU stack (Q-3), and the
compliance path coherent (AD-2) — while bounding the R-03 downside with an
explicit fallback. The AD-3 interface makes the choice **cheap to reverse**, so
committing to BUILD-first is low-regret.

**Why this is a founder decision, not an architect one:** it trades **founder
engineering time vs cash** (gateway fees) — a bootstrap-resource call — and it
sets a **recurring-cost structure that shapes pricing/margins** (the founder's
business model). This mirrors AD-5/AD-6, which were founder-ratified for the same
"only you can supply the deciding input" reason. → see the input request.

## 5. Open questions (carried to the founder / the build PoC)

- **O-1 Certificate model** *(blocks both build and buy; partly legal/founder).*
  Does each end-user supply **their own** AEAT certificate (UX + secure storage +
  RGPD burden on us), or does FacturaSimple submit as a **colaborador social** /
  with a **sello de empresa** on the user's behalf? This shapes the adapter, the
  onboarding flow, and the data-protection surface more than build-vs-buy does.
- **O-2 Obligation timeline** for the **autónomo** segment (our target) — confirm
  v1 urgency against the *current* AEAT Verifactu rollout calendar (the dates have
  moved; do not hard-code from memory — verify at build time).
- **O-3 Territorios forales** — confirm v1 is común-territory (Verifactu) **only**
  and **TicketBAI** (País Vasco/Navarra) is deferred (expected, given N-6).

## 6. Spike status

**COMPLETE.** Research + analysis persisted; build-vs-buy **direction
founder-ratified** (2026-06-15, see
`docs/input-requests/archive/2026-06-15-aeat-build-vs-buy.md`):

- **Q1 → BUILD direct, PoC-gated** (the §4 recommendation): direct AEAT
  integration as the v1 target, gated by a `preproducción` PoC; gateway adapter as
  the fallback behind the same AD-3 interface if the PoC blows its time box.
- **Q2 → user supplies their own certificate, stored securely** (encrypted at rest
  in our EU stack). Resolves **O-1**: each user holds their qualified cert; we
  store + use it on their behalf — a construction-phase requirement on the adapter
  + onboarding (added RGPD surface).
- **Q3 → gateway budget deferred** ("decide later"): calibrate the fallback at
  build time, only if the PoC stalls. Not load-bearing for this decision.
- **Q4 → no TicketBAI.** Resolves **O-3**: v1 is común-territory (Verifactu) only;
  País Vasco/Navarra foral support stays out of v1 (N-6).

Folded into **AD-3** (`proposed → accepted`) in `docs/architecture-notebook.md`
§3/§6/§7. **O-2** (autónomo obligation timeline) carried to construction as a
build-time verification. T-007 complete.

## 7. Completion verification (step 1a — graded vs. the diff)

Spike deliverable = a documented decision, not code. Graded against `plan.md`
acceptance criteria and the working-tree diff:

- ✅ Submission target characterised — `design.md §1–§2` (pre-existing, persisted).
- ✅ BUILD feasibility + PoC proof-points — `design.md §2`.
- ✅ Build-vs-buy analysis + recommendation — `design.md §3–§4`.
- ✅ **Founder ratifies the direction** — answers recorded in
  `docs/input-requests/archive/2026-06-15-aeat-build-vs-buy.md` (status `processed`).
- ✅ **AD-3 resolved `proposed → accepted`** — `architecture-notebook.md` §3 (AD-3
  decision rewritten + status `accepted`), §6, §7, and header all updated.

**Success Measures:** n/a — quick-track research/decision spike; the deliverable
is the ADR resolution itself, not instrumented behavior.
**Rollout:** n/a — no feature flag (no shipped code).
