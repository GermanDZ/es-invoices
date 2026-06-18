---
task: T-016
branch: feat/T-016-pdf-email
phase: construction
start: 2026-06-18T11:30:25Z
end: 2026-06-18T11:41:34Z
commits: [122663a, c3ffdc2]
---

# Agent Run Log — T-016 (PDF generation + send by email)

## Task
T-016 — PDF generation + send by email. New Django `documents` app (architecture-notebook §4 "Document & delivery"): render an issued invoice to a compliant PDF and deliver it by email. Standard track, solo, iteration 15.

## Commits
- `122663a` feat(T-016): invoice PDF generation + send-by-email
- `c3ffdc2` docs(T-016): sync roadmap + status, completion note

## Files changed
- Added: documents/__init__.py, documents/apps.py, documents/services.py, documents/templates/documents/invoice.html, documents/tests/__init__.py, documents/tests/test_pdf.py, documents/tests/test_email.py
- Added: docs/changes/T-016/design.md, docs/status-notes/2026-06-18-T-016.md
- Modified: config/settings.py (documents app + EMAIL_* + VERIFACTU_QR_BASE_URL), requirements.txt (weasyprint, segno, pypdf test-only)
- Modified (derived): docs/roadmap.md, docs/project-status.md
- Progress: docs/changes/T-016/plan.md (Operations boxes ticked)

## Decisions
- QR embedded as PNG data-URI (segno, no Pillow/native dep), not inline SVG — same observable behavior.
- Verifactu QR Importe = taxable_base + iva_total (IRPF not subtracted), mirroring compliance.records.
- AEAT num_serie/fecha formats replicated (not imported) to respect the compliance module boundary.
- Issuer fiscal identity passed in as a dataclass — no new account/business model.
- No "sent" status persisted (that is T-018); send_invoice_email emits a NumSerie-only instrumentation log (no recipient PII / RGPD).
- pypdf added as a test-only dependency (no requirements-dev.txt exists).

## Outcome
All 5 requirements graded ✅ against the diff; success-measure instrumentation present. 12 new tests; full suite 104 green (2 Postgres-gated skips). Write-fence and check-docs pass. Completed via /openup-complete-task.
