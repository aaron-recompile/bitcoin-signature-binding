import hashlib
from dataclasses import dataclass
from typing import Dict, List

from btcaaron import Key, TapTree


DEMO_PRIVKEY_HEX = "11" * 32
CHANGE_PRIVKEY_HEX = "22" * 32
PREV_TXID_HEX = "33" * 32
PREV_VOUT = 0
PREV_SATS = 50_000
FEE_SATS = 500


@dataclass(frozen=True)
class TxInputModel:
    txid: str
    vout: int
    amount: int
    scriptpubkey_hex: str
    sequence: int


@dataclass(frozen=True)
class TxOutputModel:
    amount: int
    scriptpubkey_hex: str


@dataclass(frozen=True)
class TxModel:
    version: int
    locktime: int
    inputs: List[TxInputModel]
    outputs: List[TxOutputModel]


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _txid_from_nowitness_hex(unsigned_hex: str) -> str:
    # txid is little-endian hash displayed in big-endian hex.
    return _double_sha256(bytes.fromhex(unsigned_hex))[::-1].hex()


def build_checksig_context() -> Dict[str, object]:
    signer = Key.from_hex(DEMO_PRIVKEY_HEX)
    change_key = Key.from_hex(CHANGE_PRIVKEY_HEX)

    program = TapTree(internal_key=signer, network="signet").checksig(signer, label="checksig").build()
    change_addr = TapTree(internal_key=change_key, network="signet").build().address

    signed_tx = (
        program.spend("checksig")
        .from_utxo(PREV_TXID_HEX, PREV_VOUT, sats=PREV_SATS)
        .to(change_addr, PREV_SATS - FEE_SATS)
        .sign(signer)
        .build()
    )

    bu_tx = signed_tx._tx
    # Unsigned txid preimage: legacy serialization without witness (`to_bytes(False)`).
    unsigned_tx_hex = bu_tx.to_bytes(False).hex()
    unsigned_txid = _txid_from_nowitness_hex(unsigned_tx_hex)
    script_pubkey_hex = program._addr_obj.to_script_pub_key().to_hex()
    input_model = TxInputModel(
        txid=bu_tx.inputs[0].txid,
        vout=bu_tx.inputs[0].txout_index,
        amount=PREV_SATS,
        scriptpubkey_hex=script_pubkey_hex,
        sequence=int.from_bytes(bu_tx.inputs[0].sequence, "little"),
    )
    output_model = TxOutputModel(
        amount=bu_tx.outputs[0].amount,
        scriptpubkey_hex=bu_tx.outputs[0].script_pubkey.to_hex(),
    )
    tx_model = TxModel(
        version=int.from_bytes(bu_tx.version, "little"),
        locktime=int.from_bytes(bu_tx.locktime, "little"),
        inputs=[input_model],
        outputs=[output_model],
    )

    leaf = program.leaf("checksig")
    witness_stack = list(bu_tx.witnesses[0].stack)

    return {
        "signer_xonly": signer.xonly,
        "address": program.address,
        "leaf_script_hex": leaf.script_hex,
        "control_block_hex": program.control_block("checksig"),
        "unsigned_tx_hex": unsigned_tx_hex,
        "unsigned_txid": unsigned_txid,
        "signed_tx_hex": signed_tx.hex,
        "tx_model": tx_model,
        "witness_stack": witness_stack,
    }
