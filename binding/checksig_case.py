"""
Case C — CHECKSIG (Tapscript): transaction / sighash binding.

Wraps the vendored taproot_checksig harness (model tx + sighash trace).
"""

from __future__ import annotations

from typing import Any, Dict

from binding.vendor.taproot_checksig.checksig_raw import run_checksig_case as _run_raw


def _hx(x: object) -> str:
    if isinstance(x, (bytes, bytearray)):
        return bytes(x).hex()
    return str(x)


def run_checksig_case() -> Dict[str, Any]:
    raw = _run_raw()
    tx_a = raw["transaction_A"]
    tx_b = raw["transaction_B_reuse_attempt"]
    chk = raw["checks"]

    return {
        "case": "CHECKSIG",
        "binding_target": "transaction",
        "key_source": "script_path_pubkey",
        "signed_object": "taproot_script_path_sighash",
        "replayable": False,
        "verification": "success" if tx_a.get("verification") else "failure",
        "short_interpretation": "Signature is over sighash(tx); change outputs => different sighash => old sig fails.",
        "subexperiments": {
            "C1_baseline": {
                "sighash_hex": _hx(tx_a["sighash"]),
                "schnorr_verify": tx_a["verification"],
            },
            "C2_reuse_other_context": {
                "sighash_b_hex": _hx(tx_b["sighash"]),
                "old_signature_still_valid": tx_b["verification"],
                "expected_false": not tx_b["verification"],
            },
        },
        "checks": chk,
        "raw": raw,
    }
