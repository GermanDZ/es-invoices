# Risk List — FacturaSimple

**Project**: FacturaSimple — compliance-first electronic invoicing for Spanish
autónomos and very small pymes.
**Phase**: Inception (iteration 2)
**Last updated**: 2026-06-15
**Owner of this list**: Product Owner (solo founder)

Risks are ranked by **exposure** (probability × impact). Probability and impact
are rated high / medium / low. Each risk has a concrete **trigger** (the
observable signal it is materializing) and a **mitigation** whose execution can
be verified. Traces from the project Vision (`docs/vision.md`, §6 Constraints &
Assumptions, §7 Risks).

## Top risks (ranked)

| ID | Risk | Prob. | Impact | Exposure | Category |
|----|------|-------|--------|----------|----------|
| R-01 | Verifactu/AEAT technical spec or deadline changes force rework of the compliance core | medium | high | **high** | Regulatory/Technical |
| R-02 | A bug produces a non-compliant invoice (legal/trust liability) | medium | high | **high** | Technical/Trust |
| R-03 | AEAT submission integration is harder/slower than expected for a small team | high | medium | **high** | Technical/Dependency |
| R-04 | Low adoption / weak willingness to pay among price-sensitive autónomos | medium | high | **high** | Business/Market |
| R-05 | Crowded competitor market (Holded, Quaderno, Sage, Declarando) crowds out a new entrant | medium | medium | medium | Market |
| R-06 | RGPD/GDPR breach or mishandling of personal + fiscal data | low | high | medium | Security/Compliance |
| R-07 | Scope creep beyond v1 overwhelms a small/bootstrapped team and delays launch past the compliance window | medium | medium | medium | Project/Capacity |
| R-08 | Tech-stack decision deferred to Elaboration constrains compliance/AEAT needs | low | medium | low | Technical/Planning |

## Risk details

### R-01 — Verifactu/AEAT spec or deadline change
- **Description**: The Verifactu / Ley Crea y Crece technical specification or its
  enforcement deadlines shift, invalidating assumptions baked into the
  compliance engine — the product's core value.
- **Probability**: medium — regulatory rollouts commonly slip or amend technical detail.
- **Impact**: high — rework of the central feature; possible launch-timing miss.
- **Trigger**: AEAT publishes a spec amendment, FAQ change, or revised deadline;
  a compliance advisor flags a divergence.
- **Mitigation**: Isolate compliance logic behind a versioned module so spec
  changes are localized; subscribe to AEAT/official channels and review monthly;
  keep a thin abstraction over the submission format. *Verifiable:* compliance
  module is a separate, versioned component; a dated monitoring log exists.
- **Owner**: Product Owner (with compliance advisor when engaged).

### R-02 — Non-compliant invoice bug
- **Description**: A defect (wrong IVA/IRPF, broken sequential numbering, malformed
  Verifactu record) yields an invoice that is not legally valid.
- **Probability**: medium — fiscal rules have many edge cases.
- **Impact**: high — user legal exposure and loss of trust in a compliance-first product.
- **Trigger**: AEAT rejects a submission; a user/gestor reports an invalid invoice;
  a regression in numbering/calculation tests.
- **Mitigation**: Comprehensive automated tests for IVA/IRPF, numbering, and
  record format, including negative/abuse cases; validate against AEAT
  test/sandbox before send; block send on validation failure. *Verifiable:* a
  test suite covering the compliance rules exists and runs in CI.
- **Owner**: Developer / Product Owner.

### R-03 — AEAT submission integration difficulty
- **Description**: Building a reliable AEAT/Verifactu submission path proves
  harder or slower than a small team can absorb.
- **Probability**: high — government integrations are notoriously fiddly (certs, formats, auth).
- **Impact**: medium — schedule risk; possible need to buy a gateway.
- **Trigger**: Integration spike exceeds its time box; sandbox auth/cert issues persist.
- **Mitigation**: Time-boxed spike in Elaboration; evaluate build-vs-buy
  (e-invoice gateway providers) early; keep submission behind an interface so a
  provider can be swapped in. *Verifiable:* a documented spike result and a
  build-vs-buy decision (ADR) exist before committing to v1 scope.
- **Owner**: Architect / Product Owner.

### R-04 — Low adoption / willingness to pay
- **Description**: Autónomos are price-sensitive and may stay with free
  spreadsheets or defer to their gestor rather than pay for FacturaSimple.
- **Probability**: medium.
- **Impact**: high — threatens business viability.
- **Trigger**: Low activation rate (<50% issue an invoice in week 1) or poor
  trial-to-paid conversion during beta.
- **Mitigation**: Validate willingness-to-pay with target users before heavy
  build; lead with the compliance-deadline value prop; instrument activation and
  time-to-first-invoice from day one; consider a free tier. *Verifiable:*
  activation + time-to-first-invoice instrumentation is live (Vision success metrics).
- **Owner**: Product Owner.

### R-05 — Crowded competitor market
- **Description**: Established players already serve this segment; a new entrant
  may struggle to be noticed.
- **Probability**: medium. **Impact**: medium.
- **Trigger**: Acquisition cost runs high; competitors ship comparable
  Verifactu-simple offerings.
- **Mitigation**: Differentiate sharply on simplicity + compliance-first
  positioning; target the under-served "I just need to invoice legally" niche;
  do not compete on breadth. *Verifiable:* positioning is reflected in v1 scope
  (no feature-bloat) and messaging.
- **Owner**: Product Owner.

### R-06 — RGPD/GDPR data breach
- **Description**: The system holds personal and fiscal data; a breach or
  mishandling carries legal and reputational consequences.
- **Probability**: low. **Impact**: high.
- **Trigger**: Security incident; failed data-protection review; data stored outside the EU.
- **Mitigation**: EU data residency; encryption at rest/in transit; least-privilege
  access; a data-protection review before launch; documented retention policy.
  *Verifiable:* a pre-launch RGPD checklist is completed and recorded.
  **Status (T-026):** Mitigation actioned — checklist completed at `docs/rgpd-checklist.md`.
  Code-side controls implemented: AES-256-GCM certificate encryption (T-011),
  production HTTPS/HSTS settings (T-026), owner-scoped data access (T-021+).
  Operator-side controls (EU hosting confirmation, DB SSL, least-privilege DB user)
  documented as runbook steps in the checklist. No ❌ items at launch gate.
- **Owner**: Product Owner / Developer.

### R-07 — Scope creep vs. small-team capacity
- **Description**: Adding out-of-scope features (quotes, expenses, payments)
  before v1 overruns the bootstrapped team and risks missing the compliance window.
- **Probability**: medium. **Impact**: medium.
- **Trigger**: v1 backlog grows beyond the agreed scope; milestones slip.
- **Mitigation**: Enforce the Vision's in/out-of-scope list (T-005 will formalize
  non-goals); defer non-core to post-v1; review scope each iteration. *Verifiable:*
  a scope + non-goals document (T-005) exists and is referenced in planning.
- **Owner**: Product Owner.

### R-08 — Deferred tech-stack decision
- **Description**: Tech stack is TODO until Elaboration; a late choice could
  conflict with compliance/AEAT integration or RGPD residency needs.
- **Probability**: low. **Impact**: medium.
- **Trigger**: Elaboration stack choice cannot meet an AEAT/RGPD constraint.
- **Mitigation**: Make the stack decision early in Elaboration with AEAT
  integration and EU-residency as explicit selection criteria; capture it as an
  ADR. *Verifiable:* an architecture decision record records the stack and its
  compliance fit.
- **Owner**: Architect / Product Owner.

---

*Self-critique: weakest point — owners are all effectively the solo founder, so
"owner" is informational rather than a true delegation; mitigations are written
to be verifiable (a test suite, a dated log, an ADR, a checklist) so they are not
mere restatements of the risk. R-03 and R-04 are the highest live exposures to
revisit each iteration. Authored in Inception (T-003); to be revisited as
Elaboration surfaces technical detail.*
