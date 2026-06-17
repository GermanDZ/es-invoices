"""Proof 2 — XSD-conformant `alta` submission (T-010, plan §R2).

Build one `registro de facturación de alta` from a sample invoice, validate it
LOCALLY against the published XSD, submit it to preproducción, and record the
per-record status (Correcto / AceptadoConErrores / Incorrecto + AEAT codes).

The submission goes to the sandbox (no tax effect). Obligado identity is derived
from the certificate subject so it matches the census. RGPD: this script prints
NO personal data (NIF/name) — only status codes, CSV, and the huella.
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import config  # noqa: E402
import alta_builder as ab  # noqa: E402

CHAIN_FILE = os.path.join(os.path.dirname(__file__), "..", "secrets", "last_alta.json")


def _now_local():
    return dt.datetime.now().astimezone()


def run(num_serie=None, chain_from=None):
    nif, nombre = config.cert_identity()
    now = _now_local()
    fecha_exp = now.strftime("%d-%m-%Y")
    fecha_hora = now.replace(microsecond=0).isoformat()
    # microsecond granularity so back-to-back runs never collide (AEAT 3000).
    num_serie = num_serie or f"POC-T010-{now.strftime('%Y%m%d%H%M%S')}-{now.microsecond:06d}"

    kwargs = dict(nif=nif, nombre=nombre, num_serie=num_serie,
                  fecha_exp=fecha_exp, fecha_hora=fecha_hora)
    if chain_from:
        kwargs.update(huella_anterior=chain_from["huella"],
                      serie_anterior=chain_from["num_serie"],
                      fecha_anterior=chain_from["fecha_exp"])
    regfactu, huella = ab.build_regfactu(**kwargs)

    ok, errors = ab.validate_local(regfactu)
    print(f"[Proof] local XSD validation: {'PASS' if ok else 'FAIL'}")
    if not ok:
        for e in errors[:8]:
            print(f"   - {e}")
        config.die("record does not validate against the local XSD — fix before submit.")
        return None

    session = config.make_session()
    payload = ab.soap_envelope(regfactu)
    print(f"[Proof] submitting NumSerie={num_serie} huella={huella[:16]}... -> {config.endpoint()}")
    resp = session.post(
        config.endpoint(), data=payload,
        headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""},
        timeout=45,
    )
    parsed = ab.parse_response(resp.text)
    print(f"[Proof] HTTP {resp.status_code}")
    for k, v in parsed.items():
        print(f"   {k}: {v}")

    estado = parsed.get("EstadoRegistro") or parsed.get("EstadoEnvio")
    return {
        "num_serie": num_serie, "fecha_exp": fecha_exp, "huella": huella,
        "http": resp.status_code, "estado": estado,
        "codigo_error": parsed.get("CodigoErrorRegistro"),
        "csv": parsed.get("CSV"), "raw": parsed,
    }


def main():
    res = run()
    if not res:
        return
    if res["estado"] in ("Correcto", "AceptadoConErrores"):
        with open(CHAIN_FILE, "w") as fh:
            json.dump(res, fh, indent=2)
        print(f"[Proof 2] PASS ({res['estado']}). Chain anchor saved for Proof 3.")
    else:
        print(f"[Proof 2] Submitted; record estado={res['estado']} "
              f"(codigo {res.get('codigo_error')}). See codes above.")


if __name__ == "__main__":
    main()
