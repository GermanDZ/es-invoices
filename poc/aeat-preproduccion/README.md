# AEAT `preproducción` submission PoC (T-010)

> **Throwaway feasibility PoC — NOT production code.** This harness exists to run
> the three proofs from `docs/changes/archive/T-007/design.md §2` against the AEAT
> VERI\*FACTU **`preproducción`** sandbox and back the BUILD-direct **AD-3**
> decision with a *running* proof (burns down residual **R-03**). The production
> submission adapter is T-014; the versioned compliance/Verifactu module is T-013;
> secure certificate storage/onboarding is T-011. Do **not** carry this code
> forward — delete it once the verdict in `docs/changes/T-010/design.md` is
> recorded.

## The three proofs (success path)

1. **Proof 1 — certificate auth** (`proofs/proof1_auth.py`): authenticate to the
   `preproducción` web service over client-certificate TLS and get a service-level
   (non-auth-rejected) response.
2. **Proof 2 — XSD-conformant `alta`** (`proofs/proof2_alta.py`): build one
   `registro de facturación de alta`, validate it locally against the published
   XSD, submit it, and get a per-record `Correcto` / `AceptadoConErrores`.
3. **Proof 3 — `huella` hash-chain** (`proofs/proof3_huella.py`): compute the
   `huella` per spec and submit a second record chained to the first; AEAT accepts
   the chain with no `encadenamiento` error.

Each proof writes its outcome (status, AEAT error codes, `huella` values) so it
can be transcribed into `docs/changes/T-010/design.md`.

## Prerequisites (founder / developer must supply)

- **A qualified certificate valid for AEAT `preproducción`** — an FNMT *test*
  certificate, or a real qualified cert exercised against the sandbox. The harness
  reads it from a **local path** given by an env var; it is **never committed**
  (see repo `.gitignore`). RGPD surface even in sandbox.
- **Network access** to the AEAT `preproducción` SOAP endpoint + its published
  WSDL/XSD.
- Python 3.11+ and the deps in `requirements.txt`.

## Configuration (env vars, no secrets in the tree)

| Var | Meaning |
|-----|---------|
| `AEAT_CERT_PATH` | Absolute path to the client certificate (`.p12`/`.pem`) — outside the repo, or under `secrets/` (git-ignored). |
| `AEAT_CERT_PASSWORD` | Cert passphrase, if any. |
| `AEAT_WSDL_URL` | Published `preproducción` WSDL URL (see "Endpoints" below). |
| `AEAT_NIF` / `AEAT_EMISOR` | Test-issuer fiscal identity for the sample records. |

## Endpoints / contract (fill at run time — verify against the current AEAT publication)

The AEAT publishes the VERI\*FACTU WSDL + XSD schemas and the `preproducción`
endpoint on the *Sede Electrónica* (Sistemas Informáticos de Facturación /
Verifactu technical area). **Resolve the exact current URLs at run time** — do not
hard-code from memory (the spec moved; see T-007 O-2). Record the URLs actually
used in `docs/changes/T-010/design.md` alongside the proof outcomes.

`config.py` centralises endpoint + cert resolution so the three proofs share one
session setup.

## Running

```bash
python3 -m venv .venv && source .venv/bin/activate   # .venv is git-ignored
pip install -r requirements.txt
export AEAT_CERT_PATH=/abs/path/to/cert.p12 AEAT_CERT_PASSWORD=...
export AEAT_WSDL_URL='https://.../preproduccion/...?wsdl'
python proofs/proof1_auth.py
python proofs/proof2_alta.py
python proofs/proof3_huella.py
```

## Time box

2 sessions (see `docs/changes/T-010/plan.md` front-matter). If a proof cannot
clear within the box, record the blocker in `design.md` and raise the **AD-3
gateway-fallback** decision via `/openup-request-input` — do not silently extend.
