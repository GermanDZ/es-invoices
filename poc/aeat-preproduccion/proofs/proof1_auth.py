"""Proof 1 — certificate auth against AEAT preproducción (T-010, plan §R1).

GOAL: open a client-certificate TLS session to the preproducción VERI*FACTU web
service and get a service-level (non-auth-rejected) SOAP response.

SKELETON — the developer wires `config.make_client()` and issues a minimal call,
then records the outcome (handshake accepted + SOAP response, or the blocker) in
docs/changes/T-010/design.md. Needs a founder-supplied cert + live sandbox.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 2)[0])  # poc/aeat-preproduccion on path
import config  # noqa: E402


def main() -> None:
    try:
        client = config.make_client()  # NotImplementedError until wired
    except config.Missing as e:
        config.die(str(e))
        return
    except NotImplementedError as e:
        config.die(f"not yet wired: {e}")
        return

    # TODO(Proof 1): issue a minimal operation on `client` and assert the TLS /
    # certificate handshake succeeded and a SOAP envelope came back (NOT a
    # TLS/auth rejection). Print the outcome for transcription into design.md.
    print("[T-010 Proof 1] client built; issue a probe call and record the outcome.")


if __name__ == "__main__":
    main()
