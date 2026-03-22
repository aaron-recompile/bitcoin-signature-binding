"""
Case B — IK + CSFS: identity binding (internal key as pubkey source).

Modeled at the cryptographic layer: verification uses P_internal instead of
witness-supplied pubkey. No separate tx digest.

Sub-experiments:
  B1 baseline — sig by K over MESSAGE verifies with P_K
  B2 wrong signer — sig by K2 over MESSAGE does not verify as K
  B3 replay — same (sig, msg) valid for two "slots" with same P_K
  B4 different identity — (sig for K) does not verify against P_K2
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict

import secp256k1
from btcaaron import Key, RawScript
from binding.vendor.inquisition_opcodes import OP_CHECKSIGFROMSTACK, OP_INTERNALKEY, build_script

# Internal-key script path leaf: OP_INTERNALKEY || OP_CHECKSIGFROMSTACK
MESSAGE = hashlib.sha256(b"binding-exp-msg:ik_csfs").digest()
K_HEX = "44" * 32
K2_HEX = "aa" * 32


def _sign(privkey_hex: str, msg32: bytes) -> str:
    pk = secp256k1.PrivateKey(bytes.fromhex(privkey_hex), raw=True)
    return pk.schnorr_sign(msg32, None, raw=True).hex()


def _verify(pub_xonly_hex: str, msg32: bytes, sig_hex: str) -> bool:
    pub = secp256k1.PublicKey(b"\x02" + bytes.fromhex(pub_xonly_hex), raw=True)
    return pub.schnorr_verify(msg32, bytes.fromhex(sig_hex), None, raw=True)


def run_ik_csfs_case() -> Dict[str, Any]:
    k = Key.from_hex(K_HEX)
    k2 = Key.from_hex(K2_HEX)
    sig_k = _sign(K_HEX, MESSAGE)
    sig_k2 = _sign(K2_HEX, MESSAGE)

    p_k = k.xonly
    p_k2 = k2.xonly

    b1 = _verify(p_k, MESSAGE, sig_k)
    b2_wrong_sig = _verify(p_k, MESSAGE, sig_k2)
    b3_slot1 = _verify(p_k, MESSAGE, sig_k)
    b3_slot2 = _verify(p_k, MESSAGE, sig_k)
    b4 = _verify(p_k2, MESSAGE, sig_k)

    leaf_script_hex = RawScript(
        build_script(OP_INTERNALKEY, OP_CHECKSIGFROMSTACK)
    ).to_hex()

    return {
        "case": "IK+CSFS",
        "binding_target": "identity",
        "key_source": "UTXO_internal_key_context",
        "signed_object": "arbitrary_32-byte_message_signed_by_internal_key",
        "script_hex": leaf_script_hex,
        "replayable_across_same_internal_key": True,
        "verification": "success" if b1 else "failure",
        "short_interpretation": "Authorization is tied to internal key P; same (sig,msg) replays if another UTXO shares P.",
        "subexperiments": {
            "B1_baseline": {"verify_sig_k_with_P_k": b1},
            "B2_wrong_signer": {
                "verify_sig_k2_with_P_k": b2_wrong_sig,
                "expected_false": not b2_wrong_sig,
            },
            "B3_replay_same_key_utxos": {
                "verify_slot_1": b3_slot1,
                "verify_slot_2": b3_slot2,
                "both_true": b3_slot1 and b3_slot2,
            },
            "B4_different_internal_key": {
                "verify_sig_k_with_P_k2": b4,
                "expected_false": not b4,
            },
        },
        "checks": {
            "identity_binding_holds": b1 and (not b2_wrong_sig) and (not b4),
            "replay_same_key": b3_slot1 and b3_slot2,
        },
    }
