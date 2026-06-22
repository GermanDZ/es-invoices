---
id: T-027-aeat-timeline
type: decision
status: approved
traces-from: [VIS-001]
---

# AEAT / Verifactu Obligation Timeline — Verified 2026-06-22

## Current Legal Deadlines (RDL 15/2025)

| Taxpayer segment | Obligation date | Basis |
|---|---|---|
| Impuesto sobre Sociedades (IS) contributors — sociedades, SL, SA, etc. | **1 January 2027** | RDL 15/2025, BOE-A-2025-24446 |
| Remaining obligated parties — autónomos (IRPF), entidades en atribución de rentas, IRNR con EP | **1 July 2027** | RDL 15/2025, BOE-A-2025-24446 |

FacturaSimple targets autónomos → **operative deadline: 1 July 2027**.

## Timeline of Changes

| Date | Instrument | Autónomo date set | Notes |
|---|---|---|---|
| 2023-12-05 | RD 1007/2023 | 1 July 2025 | Original Verifactu regulation |
| 2025-01 (approx.) | RD 254/2025 | 1 July 2026 | First extension; sociedades → 1 Jan 2026 |
| 2025-12-02 | RDL 15/2025 (BOE-A-2025-24446) | **1 July 2027** | Second extension; sociedades → 1 Jan 2027 |

## 2026 Status

The period from now (June 2026) through the obligation dates is a **voluntary testing period**. Obligated parties may submit Verifactu records voluntarily; non-Verifactu SIF may still be used until the deadline.

## Codebase Hard-Coded Dates — Scan Result

Scanned: `invoicing/`, `compliance/`, `aeat/`, `accounts/`, `clients/`, `submission/` (all production `.py` files, excluding test files and migrations). **No obligation or regulatory deadline dates found hard-coded.**

Dates found in test fixtures:
- `compliance/tests/factories.py:37` — `.not_valid_before(datetime.datetime(2026, 1, 1))`: certificate validity date for test certs only, not a regulatory deadline.
- `compliance/tests/test_signing.py:32` — `fecha_exp="18-06-2026"`: certificate expiry in a signing test fixture, not a regulatory deadline.

**Verdict: ✅ No hard-coded obligation dates in production code.**

## Official Sources

- [AEAT Nota Informativa — Ampliación del plazo (RDL 15/2025)](https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/nota-informativa-ampliacion-plazo-adaptacion-facturacion.html)
- [BOE-A-2025-24446 — RDL 15/2025 full text](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-24446)
- [Noticias Jurídicas — Nueva prórroga Verifactu 2027](https://noticias.juridicas.com/actualidad/noticias/20735-nueva-prorroga:-verifactu-no-sera-obligatorio-hasta-2027-para-sociedades-y-otros-contribuyentes/)
