"""Proof 2 — XSD-conformant `alta` submission (T-010, plan §R2).

GOAL: build one `registro de facturación de alta`, validate it locally against
the published XSD BEFORE sending, submit it, and get a per-record `Correcto` /
`AceptadoConErrores` (i.e. schema-accepted, not `Incorrecto` for a structural
reason).

SKELETON — depends on Proof 1's wired client. Steps the developer fills:
  1. Load the published `alta` XSD (URL/path from config / README "Endpoints").
  2. Build a sample `alta` from a fixture invoice (lxml).
  3. lxml.etree.XMLSchema validation locally — fail fast if non-conformant.
  4. Submit via the zeep client; capture per-record status + AEAT error codes.
  5. Record status + the record's `huella` in design.md (Proof 3 chains off it).
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])
import config  # noqa: E402


def main() -> None:
    try:
        config.make_client()
    except config.Missing as e:
        config.die(str(e))
    except NotImplementedError as e:
        config.die(f"not yet wired (do Proof 1 first): {e}")
    # TODO(Proof 2): build → validate vs XSD → submit → record status + huella.
    print("[T-010 Proof 2] build/validate/submit an `alta`; record status + huella.")


if __name__ == "__main__":
    main()
