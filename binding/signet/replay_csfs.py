"""
Signet — CSFS replay: two funds to the same P2TR+CSFS lock, two spends with the same witness.

  PYTHONPATH=. python -m binding.signet.replay_csfs --fund-twice
  PYTHONPATH=. python -m binding.signet.replay_csfs --spend [--input-txid TXID]
  (repeat --spend for the second UTXO, or pass --input-txid for the second fund tx)

Uses MESSAGE = SHA256(b\"binding-exp-msg:csfs\") to match offline csfs_case.py.
"""

from __future__ import annotations

import argparse
import sys

from btcaaron import Key, RawScript, TapTree, wif_secret_bytes

# OP_CHECKSIGFROMSTACK — witness [sig, msg32, pubkey_xonly]
_CSFS_LEAF = RawScript("cc")
from binding.template_common import broadcast_or_raise, default_change_address, fund_address
from secp256k1 import PrivateKey

from binding.signet._common import (
    MESSAGE_CSFS,
    SIGNET_DIR,
    list_utxos_for_address,
    load_demo_wif,
    read_state,
    utxo_from_funding_txid,
    write_state,
)

STATE_FILE = "state_replay_csfs.json"
FUND_HINT_FILE = str(SIGNET_DIR / ".replay_csfs_last_fund_txid")


def _make_witness(wif: str) -> list[str]:
    secret = wif_secret_bytes(wif)
    pk = PrivateKey(secret, raw=True)
    sig = pk.schnorr_sign(MESSAGE_CSFS, None, raw=True)
    pub_x = pk.pubkey.serialize()[1:33]
    return [sig.hex(), MESSAGE_CSFS.hex(), pub_x.hex()]


def _program(wif: str):
    key = Key.from_wif(wif)
    return (
        TapTree(internal_key=key, network="signet").custom(script=_CSFS_LEAF, label="csfs").build()
    )


def cmd_fund_twice(wif: str) -> None:
    prog = _program(wif)
    addr = prog.address
    t1 = fund_address(addr, FUND_HINT_FILE, fund_sats=50_000)
    t2 = fund_address(addr, FUND_HINT_FILE, fund_sats=50_000)
    st = read_state(STATE_FILE)
    st.update(
        {
            "demo": "replay_csfs",
            "address": addr,
            "message_label": "binding-exp-msg:csfs",
            "fund_txids": [t1, t2],
        }
    )
    write_state(STATE_FILE, st)
    print("Fund #1 txid:", t1)
    print("Fund #2 txid:", t2)
    print("Same witness will unlock both UTXOs (different prevouts).")


def cmd_spend(wif: str, input_txid: str | None, fee_sats: int) -> None:
    prog = _program(wif)
    addr = prog.address
    witness = _make_witness(wif)

    chosen: tuple[str, int, int] | None = None
    if input_txid:
        chosen = utxo_from_funding_txid(addr, input_txid)

    if chosen is None:
        utxos = list_utxos_for_address(addr)
        if not utxos:
            print(
                "No UTXO at address. If you just funded, wait for 1 confirmation or use --input-txid "
                "(getrawtransaction path).",
                file=sys.stderr,
            )
            sys.exit(1)
        if input_txid:
            for u in utxos:
                if u[0] == input_txid:
                    chosen = u
                    break
            if not chosen:
                print(f"No unspent output for txid {input_txid} at {addr}", file=sys.stderr)
                sys.exit(1)
        else:
            if len(utxos) > 1:
                print("Multiple UTXOs; pass --input-txid to choose one:", file=sys.stderr)
                for u in utxos:
                    print(f"  {u[0]}:{u[1]} ({u[2]} sats)", file=sys.stderr)
                sys.exit(1)
            chosen = utxos[0]

    txid, vout, sats = chosen
    if fee_sats <= 0 or fee_sats >= sats:
        raise SystemExit(f"Invalid fee_sats={fee_sats} for input sats={sats}")
    change = default_change_address()
    tx = (
        prog.spend("csfs")
        .from_utxo(txid, vout, sats=sats)
        .to(change, sats - fee_sats)
        .unlock_with(witness)
        .build()
    )
    out = broadcast_or_raise(tx.hex)
    print("Reveal txid:", out)
    print("(Same stack as any other spend with this MESSAGE + signer key.)")


def main() -> None:
    parser = argparse.ArgumentParser(description="CSFS Signet replay (two funds, same witness)")
    parser.add_argument("--fund-twice", action="store_true", help="Send two 50k sats txs to the CSFS address")
    parser.add_argument(
        "--spend",
        action="store_true",
        help="Spend one UTXO at the CSFS address using the fixed witness",
    )
    parser.add_argument("--input-txid", metavar="TXID", help="Which fund tx to spend (required if multiple UTXOs)")
    parser.add_argument("--fee-sats", type=int, default=500)
    args = parser.parse_args()
    wif = load_demo_wif()

    if args.fund_twice:
        cmd_fund_twice(wif)
    elif args.spend:
        cmd_spend(wif, args.input_txid, args.fee_sats)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
