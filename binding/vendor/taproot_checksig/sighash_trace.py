import hashlib
import struct
from typing import Dict, List, Tuple

import secp256k1

from .tx_builder import TxInputModel, TxModel, TxOutputModel


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _tagged_hash(tag: str, data: bytes) -> bytes:
    t = _sha256(tag.encode("ascii"))
    return _sha256(t + t + data)


def _compact_size(n: int) -> bytes:
    if n < 0xFD:
        return bytes([n])
    if n <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", n)
    if n <= 0xFFFFFFFF:
        return b"\xfe" + struct.pack("<I", n)
    return b"\xff" + struct.pack("<Q", n)


def _ser_string(data: bytes) -> bytes:
    return _compact_size(len(data)) + data


def _ser_outpoint(inp: TxInputModel) -> bytes:
    return bytes.fromhex(inp.txid)[::-1] + struct.pack("<I", inp.vout)


def _ser_txout(out: TxOutputModel) -> bytes:
    return struct.pack("<q", out.amount) + _ser_string(bytes.fromhex(out.scriptpubkey_hex))


def compute_taproot_script_path_trace(
    tx: TxModel,
    *,
    input_index: int,
    tapleaf_script_hex: str,
    key_version: int = 0x00,
    codeseparator_pos: int = 0xFFFFFFFF,
    hash_type: int = 0x00,
    annex_present: bool = False,
    include_debug: bool = False,
) -> Dict[str, object]:
    prevouts_blob = b"".join(_ser_outpoint(i) for i in tx.inputs)
    amounts_blob = b"".join(struct.pack("<q", i.amount) for i in tx.inputs)
    scriptpubkeys_blob = b"".join(_ser_string(bytes.fromhex(i.scriptpubkey_hex)) for i in tx.inputs)
    sequences_blob = b"".join(struct.pack("<I", i.sequence) for i in tx.inputs)
    outputs_blob = b"".join(_ser_txout(o) for o in tx.outputs)

    hash_prevouts = _sha256(prevouts_blob)
    hash_amounts = _sha256(amounts_blob)
    hash_scriptpubkeys = _sha256(scriptpubkeys_blob)
    hash_sequences = _sha256(sequences_blob)
    hash_outputs = _sha256(outputs_blob)

    script_bytes = bytes.fromhex(tapleaf_script_hex)
    tapleaf_preimage = bytes([0xC0]) + _compact_size(len(script_bytes)) + script_bytes
    tapleaf_hash = _tagged_hash("TapLeaf", tapleaf_preimage)

    ext_flag = 1  # tapscript spend
    spend_type = ext_flag * 2 + (1 if annex_present else 0)

    sighash_msg = (
        b"\x00"  # sighash epoch
        + bytes([hash_type])
        + struct.pack("<I", tx.version)
        + struct.pack("<I", tx.locktime)
        + hash_prevouts
        + hash_amounts
        + hash_scriptpubkeys
        + hash_sequences
        + hash_outputs
        + bytes([spend_type])
        + struct.pack("<I", input_index)
        + tapleaf_hash
        + bytes([key_version])
        + struct.pack("<I", codeseparator_pos)
    )
    final_sighash = _tagged_hash("TapSighash", sighash_msg)

    result = {
        "version": tx.version,
        "locktime": tx.locktime,
        "hashPrevouts": hash_prevouts.hex(),
        "hashAmounts": hash_amounts.hex(),
        "hashScriptPubKeys": hash_scriptpubkeys.hex(),
        "hashSequences": hash_sequences.hex(),
        "hashOutputs": hash_outputs.hex(),
        "spend_type": spend_type,
        "input_index": input_index,
        "tapleaf_hash": tapleaf_hash.hex(),
        "key_version": key_version,
        "codeseparator_pos": codeseparator_pos,
        "final_sighash": final_sighash.hex(),
    }

    if include_debug:
        result["debug"] = {
            "input_prevouts_serialized": prevouts_blob.hex(),
            "input_amounts_serialized": amounts_blob.hex(),
            "input_scriptpubkeys_serialized": scriptpubkeys_blob.hex(),
            "input_sequences_serialized": sequences_blob.hex(),
            "outputs_serialized": outputs_blob.hex(),
            "tapleaf_preimage": tapleaf_preimage.hex(),
            "sighash_message": sighash_msg.hex(),
            "hash_type": hash_type,
            "annex_present": annex_present,
            "ext_flag": ext_flag,
        }

    return result


def parse_taproot_signature(signature_hex: str) -> Tuple[bytes, int]:
    sig = bytes.fromhex(signature_hex)
    if len(sig) == 64:
        return sig, 0x00
    if len(sig) == 65:
        return sig[:64], sig[64]
    raise ValueError(f"Unexpected taproot signature length: {len(sig)}")


def verify_schnorr_signature(pubkey_xonly_hex: str, sighash_hex: str, signature_hex: str) -> bool:
    sig64, _ = parse_taproot_signature(signature_hex)
    pubkey = secp256k1.PublicKey(b"\x02" + bytes.fromhex(pubkey_xonly_hex), raw=True)
    return pubkey.schnorr_verify(bytes.fromhex(sighash_hex), sig64, None, raw=True)


def verify_schnorr_signature_debug(pubkey_xonly_hex: str, sighash_hex: str, signature_hex: str) -> Dict[str, object]:
    sig64, sighash_type = parse_taproot_signature(signature_hex)
    pubkey_bytes = b"\x02" + bytes.fromhex(pubkey_xonly_hex)
    sighash_bytes = bytes.fromhex(sighash_hex)
    pubkey = secp256k1.PublicKey(pubkey_bytes, raw=True)
    verified = pubkey.schnorr_verify(sighash_bytes, sig64, None, raw=True)
    return {
        "pubkey_xonly_hex": pubkey_xonly_hex,
        "pubkey_compressed_hex": pubkey_bytes.hex(),
        "signature_hex_raw": signature_hex,
        "signature_hex_64": sig64.hex(),
        "signature_len_raw": len(bytes.fromhex(signature_hex)),
        "signature_len_used": len(sig64),
        "sighash_type_byte": sighash_type,
        "message_hex": sighash_hex,
        "verified": verified,
    }


def dissect_sighash_message(sighash_message_hex: str) -> Dict[str, object]:
    msg = bytes.fromhex(sighash_message_hex)
    expected_len = 212
    if len(msg) != expected_len:
        raise ValueError(f"Unexpected sighash_message length: {len(msg)} (expected {expected_len})")

    layout = [
        ("epoch", 1),
        ("hash_type", 1),
        ("version", 4),
        ("locktime", 4),
        ("hashPrevouts", 32),
        ("hashAmounts", 32),
        ("hashScriptPubKeys", 32),
        ("hashSequences", 32),
        ("hashOutputs", 32),
        ("spend_type", 1),
        ("input_index", 4),
        ("tapleaf_hash", 32),
        ("key_version", 1),
        ("codeseparator_pos", 4),
    ]

    offset = 0
    rows = []
    for name, size in layout:
        part = msg[offset: offset + size]
        rows.append(
            {
                "field": name,
                "offset_start": offset,
                "offset_end_exclusive": offset + size,
                "size_bytes": size,
                "hex": part.hex(),
            }
        )
        offset += size

    return {
        "total_size_bytes": len(msg),
        "total_size_hex_chars": len(sighash_message_hex),
        "rows": rows,
    }
