---
id: T-027
title: "Verify AEAT obligation timeline vs current rollout calendar (O-2)"
type: work-item
status: in-progress
track: quick
hat: developer
touches: ["docs/"]
depends-on: []
---

# T-027 — Verify AEAT Obligation Timeline (O-2)

## Reason

The architecture notebook carried an O-2 open question: confirm the exact autónomo
Verifactu obligation date against the current AEAT rollout calendar. Shipping with a
stale or hard-coded date would mislead users and potentially require an emergency patch.

## Expected Outcome

- A dated summary in `docs/changes/T-027/` recording the verified timeline.
- Confirmation that no obligation date is hard-coded in the codebase.
- R-02 (regulatory timeline risk) in `docs/risk-list.md` updated to reflect findings.

## Operations

- [x] (developer) Search codebase for hard-coded obligation dates.
- [x] (developer) Research current AEAT/Verifactu rollout calendar.
- [x] (developer) Author `docs/changes/T-027/aeat-timeline.md` with verified dates and source.
- [x] (developer) Update `docs/risk-list.md` §R-01 with current timeline evidence.
- [x] (developer) Commit changes.
