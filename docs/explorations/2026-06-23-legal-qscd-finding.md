# Finding: Verifactu signature & QSCD requirement (legal probe)

**Date:** 2026-06-23
**Probe for:** `docs/explorations/2026-06-23-browser-side-signing.md` →
"[legal, blocking]" open question (2026-06-23 security-first revision).
**Question:** Does Verifactu require a QSCD-backed *qualified* electronic
signature, or accept an *advanced* signature from a qualified certificate — and
does that gate the browser JS-upload (software P12) signing path?

## Verdict (two parts)

**1. Verifactu mode requires NO per-record electronic signature at all.**
This project submits `RegistroAlta` / `RegistroAnulacion` to AEAT — i.e. it
operates in **VERI\*FACTU mode**. AEAT's own FAQ is explicit:

> "La modalidad VERI\*FACTU no contempla como requisito la firma electrónica de
> los registros de facturación a remitir." … "Precisamente, una de las ventajas
> de utilizar VERI\*FACTU es la ausencia de esta obligación."
> — [AEAT FAQ, Sistemas VERI\*FACTU][aeat-faq]

Integrity in Verifactu mode is provided by the **hash chain (`huella` /
encadenamiento) plus immediate, reliable remission to AEAT**, not by a
per-record signature. The electronic signature is mandatory only for
**NO-VERI\*FACTU** systems (records stored in the SIF, or sent on
*requerimiento*) — RD 1007/2023's two-modality split.

**2. Even where a signature IS required (NO-Verifactu), no QSCD is mandated.**
Orden HAC/1177/2024 requires the record signature to be a **XAdES Enveloped
Signature** per **ETSI EN 319 132**, generated with a private key associated to
a **"certificado electrónico cualificado de firma electrónica"** (or, for legal
persons, a *sello electrónico* certificate) from a QTSP on the EU Trusted List
under eIDAS (Reg. (UE) 910/2014). The text requires a **qualified
certificate** — it does **not** require a **QSCD** (no "dispositivo cualificado
de creación de firma/sello" language). The mandated artefact is therefore an
**advanced** electronic signature/seal **based on a qualified certificate**, not
a **qualified** electronic signature (QES) in the eIDAS Art. 3(12) sense.
A **software-held P12 key satisfies this** — no hardware token is legally
required. ([Orden HAC/1177/2024 / BOE-A-2024-22138][boe]; expert reading of the
provision, incl. the firma-vs-sello point: [inza.blog][inza].)

## Impact on the dual-track design

- **The JS-upload path is legally cleared.** No QSCD mandate → browser
  software-signing of a P12 key produces a valid signature wherever a signature
  is required at all. The legal blocker the revision flagged is **resolved
  favourably**; it does **not** force the AutoFirma/hardware-token path.
- **AutoFirma/hardware token becomes a *security* preference, not a *compliance*
  necessity.** Its value is the stronger custody / WYSIWYS story (revision §"Two
  structural threats"), kept as the high-assurance arm of the dual track on
  security grounds — not because the law demands a QSCD.
- **Bigger reframing (flag, not resolved here):** for this project's actual
  Verifactu flow, per-record XAdES is **not legally required**. AEAT
  authenticates the *submission channel* with the user's certificate; the
  registros carry the hash chain, not a XAdES signature. The existing
  `compliance/signing.py` per-record XAdES-BES may be (a) groundwork for a future
  NO-Verifactu mode, or (b) more than Verifactu submission needs. This
  materially affects the browser-signing exploration's premise and deserves its
  own follow-up before scoping any signing iteration.

## Confidence & caveats

- Part 1 (Verifactu = no signature) is **high confidence** — stated directly by
  AEAT's published FAQ.
- Part 2 (no QSCD mandated) is **high confidence on the regulatory text** (it
  names only a qualified *certificate*, with no QSCD clause) but is an
  *interpretation*; **legal counsel should ratify** before it is relied on as a
  compliance position, and should confirm the channel-authentication certificate
  requirements for the AEAT webservice.

## Sources

- [AEAT — Preguntas frecuentes, Sistemas VERI\*FACTU][aeat-faq]
- [Orden HAC/1177/2024 (BOE-A-2024-22138), consolidado][boe]
- [inza.blog — firma XAdES Enveloped / ETSI EN 319 132 para la Orden HAC/1177/2024][inza]

[aeat-faq]: https://sede.agenciatributaria.gob.es/Sede/iva/sistemas-informaticos-facturacion-verifactu/preguntas-frecuentes/sistemas-verifactu.html
[boe]: https://www.boe.es/buscar/act.php?id=BOE-A-2024-22138
[inza]: https://inza.blog/2024/11/24/firma-de-tipo-xades-enveloped-signature-segun-etsi-en-319-132-para-cumplir-la-orden-hac-1177-2024-de-17-de-octubre/
