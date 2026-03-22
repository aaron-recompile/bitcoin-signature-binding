"""
Case A — CSFS: message binding; pubkey from witness.

Sub-experiments:
  A1 baseline success
  A2 same (sig, msg, pubkey) reused across two different synthetic tx contexts
  A3 mutation failure (tampered message or wrong pubkey)
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict

import secp256k1
from btcaaron import Key, RawScript, TapTree

# OP_CHECKSIGFROMSTACK (same as btcaaron `inq_csfs_script()` when available).
_CSFS_LEAF = RawScript("cc")

INTERNAL_PRIVKEY_HEX = "55" * 32
DEST_PRIVKEY_HEX = "66" * 32
SIGNER_PRIVKEY_HEX = "44" * 32
MESSAGE = hashlib.sha256(b"binding-exp-msg:csfs").digest()


def _sign(privkey_hex: str, msg32: bytes) -> str:
    pk = secp256k1.PrivateKey(bytes.fromhex(privkey_hex), raw=True)
    return pk.schnorr_sign(msg32, None, raw=True).hex()


def _verify(pub_xonly_hex: str, msg32: bytes, sig_hex: str) -> bool:
    pub = secp256k1.PublicKey(b"\x02" + bytes.fromhex(pub_xonly_hex), raw=True)
    return pub.schnorr_verify(msg32, bytes.fromhex(sig_hex), None, raw=True)


def _build_csfs_spend(prev_txid: str, prev_sats: int, witness_stack: list[str]) -> Dict[str, Any]:
    internal_key = Key.from_hex(INTERNAL_PRIVKEY_HEX)
    dest_key = Key.from_hex(DEST_PRIVKEY_HEX)
    program = TapTree(internal_key=internal_key, network="signet").custom(
        script=_CSFS_LEAF,
        label="csfs",
    ).build()
    dest_addr = TapTree(internal_key=dest_key, network="signet").build().address
    tx = (
        program.spend("csfs")
        .from_utxo(prev_txid, 0, sats=prev_sats)
        .to(dest_addr, prev_sats - 500)
        .unlock_with(witness_stack)
        .build()
    )
    return {
        "address": program.address,
        "tx_hex": tx.hex,
        "leaf_script_hex": program.leaf("csfs").script_hex,
        "witness": list(tx._tx.witnesses[0].stack),
        "output_amount": prev_sats - 500,
    }


def run_csfs_case() -> Dict[str, Any]:
    signer = Key.from_hex(SIGNER_PRIVKEY_HEX)
    sig_hex = _sign(SIGNER_PRIVKEY_HEX, MESSAGE)
    witness = [sig_hex, MESSAGE.hex(), signer.xonly]

    tx_a = _build_csfs_spend("77" * 32, 50_000, witness)
    tx_b = _build_csfs_spend("88" * 32, 61_000, witness)

    ok_a = _verify(signer.xonly, MESSAGE, sig_hex)
    ok_b = _verify(signer.xonly, MESSAGE, sig_hex)

    bad_msg = bytearray(MESSAGE)
    bad_msg[0] ^= 0x01
    msg_tamper_ok = _verify(signer.xonly, bytes(bad_msg), sig_hex)

    # Use another *valid* x-only pubkey (flipping bits can leave the curve → secp256k1 rejects).
    other_key = Key.from_hex(INTERNAL_PRIVKEY_HEX)
    wrong_pub_xonly = other_key.xonly
    pubkey_mismatch_ok = _verify(wrong_pub_xonly, MESSAGE, sig_hex)

    return {
        "case": "CSFS",
        "binding_target": "message",
        "key_source": "witness",
        "signed_object": "arbitrary_32-byte_message",
        "script_hex": tx_a["leaf_script_hex"],
        "replayable": True,
        "verification": "success" if ok_a else "failure",
        "short_interpretation": "Same signature verifies the same message for any compatible tapscript; tx id differs.",
        "subexperiments": {
            "A1_baseline": {
                "txid_synthetic": "77" * 32,
                "schnorr_verify_message": ok_a,
            },
            "A2_reuse_same_sig_msg_pubkey": {
                "txid_synthetic_B": "88" * 32,
                "schnorr_verify_message": ok_b,
                "same_stack_reused": True,
            },
            "A3_mutation_failures": {
                "message_tampered_verify": msg_tamper_ok,
                "wrong_pubkey_verify": pubkey_mismatch_ok,
                "wrong_pubkey_note": "valid x-only from another key; sig was for signer key",
                "expected_both_false": not msg_tamper_ok and not pubkey_mismatch_ok,
            },
        },
        "artifacts": {
            "tx_a_hex": tx_a["tx_hex"],
            "tx_b_hex": tx_b["tx_hex"],
            "witness_template": witness,
        },
        "checks": {
            "reuse_passes_for_csfs": bool(ok_a and ok_b),
            "mutations_fail": (not msg_tamper_ok) and (not pubkey_mismatch_ok),
        },
    }
