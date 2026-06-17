"""Proof 3 — `huella` hash-chain (T-010, plan §R3).

Submit a SECOND `alta` that carries the first record's `huella` as its
predecessor link (`Encadenamiento/RegistroAnterior`), and assert AEAT accepts the
chain with NO `encadenamiento`/`huella` error. Records BOTH huella values.

Depends on Proof 2 having saved an accepted first record to secrets/last_alta.json.
"""
import json
import os
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import config  # noqa: E402
import proof2_alta as p2  # noqa: E402

CHAIN_FILE = os.path.join(os.path.dirname(__file__), "..", "secrets", "last_alta.json")


def main():
    if not os.path.isfile(CHAIN_FILE):
        config.die("no secrets/last_alta.json — run Proof 2 first to anchor the chain.")
        return
    with open(CHAIN_FILE) as fh:
        first = json.load(fh)

    print(f"[Proof 3] chaining onto first record: NumSerie={first['num_serie']} "
          f"huella={first['huella'][:16]}...")
    res = p2.run(chain_from=first)   # reuse the build+validate+submit pipeline
    if not res:
        return

    print("\n[Proof 3] chain result:")
    print(f"   first.huella : {first['huella']}")
    print(f"   second.huella: {res['huella']}")
    print(f"   second.estado: {res['estado']}  csv={res.get('csv')}  "
          f"codigo={res.get('codigo_error')}")

    chain_err = (res.get("codigo_error") and
                 "encaden" in (res["raw"].get("DescripcionErrorRegistro", "").lower()))
    if res["estado"] == "Correcto":
        print("[Proof 3] PASS: AEAT accepted the chained record (no encadenamiento error).")
    elif res["estado"] == "AceptadoConErrores" and not chain_err:
        print("[Proof 3] PASS (with non-chain warnings): chaining accepted; "
              "see codes for unrelated warnings.")
    else:
        print("[Proof 3] FAIL: chained record rejected — inspect the code above "
              "(encadenamiento error?).")


if __name__ == "__main__":
    main()
