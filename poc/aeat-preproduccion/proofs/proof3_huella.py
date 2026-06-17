"""Proof 3 — `huella` hash-chain (T-010, plan §R3).

GOAL: compute the `huella` per the AEAT spec and submit a SECOND record (a second
`alta` or an `anulación`) that carries the prior record's `huella` as its
predecessor link; AEAT accepts the chain with NO `encadenamiento`/`huella` error.

SKELETON — depends on a first record accepted in Proof 2. Steps the developer
fills:
  1. Take the first record + its `huella` (from Proof 2 output).
  2. Compute the second record's `huella` over the spec-defined field
     concatenation (hashlib; exact field list + order per the published spec).
  3. Embed the first record's `huella` as the predecessor reference.
  4. Submit; assert no chain error; record BOTH `huella` values in design.md.
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
        config.die(f"not yet wired (do Proofs 1-2 first): {e}")
    # TODO(Proof 3): chain second record off the first huella; submit; record both.
    print("[T-010 Proof 3] chain a second record; assert no encadenamiento error.")


if __name__ == "__main__":
    main()
