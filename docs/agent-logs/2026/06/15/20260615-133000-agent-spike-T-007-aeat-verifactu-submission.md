# Agent Run — T-007 AEAT/Verifactu submission spike (completion)

- **Task**: T-007 — AEAT/Verifactu submission spike (build-vs-buy)
- **Branch**: spike/T-007-aeat-verifactu-submission
- **Phase**: elaboration
- **Track**: quick
- **Event**: iteration_complete (resume of suspended lane → fold founder decision → complete)
- **Start**: 2026-06-15
- **End**: 2026-06-15
- **Commit(s)**: d27ef2b — docs(arch): resolve AD-3 (BUILD direct, PoC-gated) — founder-ratified AEAT build-vs-buy [T-007]

## Files changed
- docs/architecture-notebook.md (AD-3 proposed → accepted; §3/§6/§7 + header)
- docs/changes/T-007/design.md (founder answers folded; §6 status, §7 verification)
- docs/changes/T-007/plan.md (boxes ticked; awaiting-input removed; touches widened)
- docs/input-requests/archive/2026-06-15-aeat-build-vs-buy.md (answers recorded; processed; archived)

## Decisions
- **AD-3 resolved** `proposed → accepted`: BUILD direct AEAT VERI*FACTU integration,
  PoC-gated, with a gateway adapter fallback behind the same interface.
- **O-1 (certificate model)**: user supplies own qualified cert; stored securely (encrypted at rest, EU stack).
- **O-3 (scope)**: común-territory Verifactu only; no TicketBAI / foral support in v1.
- **O-2 (obligation timeline)**: carried to construction as a build-time verification.
- Direction founder-ratified via archived input request 2026-06-15-aeat-build-vs-buy.md.
