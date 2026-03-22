from dataclasses import replace
from typing import Dict

from .sighash_trace import (
    compute_taproot_script_path_trace,
    verify_schnorr_signature,
)
from .tx_builder import build_checksig_context
from .witness_decoder import (
    decode_tapscript_checksig,
    decode_witness_stack,
)


def run_checksig_case() -> Dict[str, object]:
    ctx = build_checksig_context()
    tx_model = ctx["tx_model"]
    leaf_script_hex = ctx["leaf_script_hex"]
    witness = decode_witness_stack(ctx["witness_stack"])
    tapscript = decode_tapscript_checksig(witness["tapscript"])

    trace_a = compute_taproot_script_path_trace(
        tx_model,
        input_index=0,
        tapleaf_script_hex=leaf_script_hex,
    )
    verify_a = verify_schnorr_signature(
        tapscript["pubkey_xonly"],
        trace_a["final_sighash"],
        witness["signature"],
    )

    # Reuse demo under CHECKSIG: change tx output amount and test old signature.
    out0 = tx_model.outputs[0]
    tx_b = replace(
        tx_model,
        outputs=[replace(out0, amount=out0.amount - 100)],
    )
    trace_b = compute_taproot_script_path_trace(
        tx_b,
        input_index=0,
        tapleaf_script_hex=leaf_script_hex,
    )
    verify_b_with_old_sig = verify_schnorr_signature(
        tapscript["pubkey_xonly"],
        trace_b["final_sighash"],
        witness["signature"],
    )

    return {
        "transaction_A": {
            "sighash": trace_a["final_sighash"],
            "signature": witness["signature"],
            "verification": verify_a,
        },
        "transaction_B_reuse_attempt": {
            "sighash": trace_b["final_sighash"],
            "reused_signature": witness["signature"],
            "verification": verify_b_with_old_sig,
        },
        "checks": {
            "sighash_changed": trace_a["final_sighash"] != trace_b["final_sighash"],
            "reuse_fails_for_checksig": (verify_a is True and verify_b_with_old_sig is False),
        },
    }
