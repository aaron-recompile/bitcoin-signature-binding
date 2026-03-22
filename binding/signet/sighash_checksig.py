"""
Signet — CHECKSIG binding: (1) valid Tapscript CHECKSIG spend, (2) same signature on a
mutated tx (different output amount) must be rejected by the node.

Flow:
  --fund          fund the P2TR script-path CHECKSIG address
  --demo          build tx A (signed), tx B (reused sig, smaller output), testmempoolaccept;
                  broadcast tx A only if B is rejected as expected

Uses a TapTree leaf <xonly> OP_CHECKSIG (see btcaaron TapTree.checksig).

  PYTHONPATH=. python -m binding.signet.sighash_checksig --fund
  PYTHONPATH=. python -m binding.signet.sighash_checksig --demo
"""

from __future__ import annotations

import argparse
import copy
import json
import sys

from btcaaron import Key, TapTree
from binding.rpc_config import rpc
from binding.template_common import (
    broadcast_or_raise,
    default_change_address,
    find_template_utxo_or_exit,
    fund_address,
    read_txid_hint,
)
from binding.signet._common import SIGNET_DIR, load_demo_wif, read_state, write_state

FUND_FILE = str(SIGNET_DIR / ".sighash_checksig_fund_txid")
STATE_FILE = "state_sighash_checksig.json"


def cmd_fund(wif: str) -> None:
    key = Key.from_wif(wif)
    program = TapTree(internal_key=key, network="signet").checksig(key, label="chk").build()
    addr = program.address
    txid = fund_address(addr, FUND_FILE, fund_sats=50_000)
    st = read_state(STATE_FILE)
    st.update({"demo": "sighash_checksig", "address": addr, "fund_txid": txid})
    write_state(STATE_FILE, st)
    print("Fund txid:", txid)
    print("Address:", addr)


def cmd_demo(wif: str, fee_sats: int, delta_sats: int, dry_run: bool) -> None:
    key = Key.from_wif(wif)
    program = TapTree(internal_key=key, network="signet").checksig(key, label="chk").build()
    addr = program.address
    change = default_change_address()

    hint = read_txid_hint(None, FUND_FILE)
    utxo = find_template_utxo_or_exit(addr, hint)
    txid, vout, sats = utxo
    if fee_sats + delta_sats >= sats:
        raise SystemExit(f"Need input sats > fee + delta (sats={sats}, fee={fee_sats}, delta={delta_sats})")

    out_a = sats - fee_sats
    out_b = sats - fee_sats - delta_sats  # different output => different sighash

    tx_a = (
        program.spend("chk")
        .from_utxo(txid, vout, sats=sats)
        .to(change, out_a)
        .sign(key)
        .build()
    )

    # Reuse tx A's witness on a tx that differs only in output amount (wrong sighash).
    # NOTE: `SpendBuilder` / unsigned tx layout is btcaaron-internal (`_tx`). Pin or note your
    # `btcaaron` version in releases; upgrading the library may require adjusting this access.
    bu_b = copy.deepcopy(tx_a._tx)
    bu_b.outputs[0].amount = out_b
    hex_b = bu_b.serialize()

    res_b = rpc("testmempoolaccept", [hex_b])
    res_a = rpc("testmempoolaccept", [tx_a.hex])

    print("--- testmempoolaccept (mutated tx, reused signature from tx A) ---")
    print(json.dumps(res_b, indent=2))
    print("--- testmempoolaccept (original signed tx A) ---")
    print(json.dumps(res_a, indent=2))

    ok_b_rejected = False
    if isinstance(res_b, list) and res_b:
        ok_b_rejected = not res_b[0].get("allowed", False)
    ok_a_ok = isinstance(res_a, list) and res_a and res_a[0].get("allowed", False)

    if not ok_b_rejected:
        print("Expected: mutated tx B rejected. Got above.", file=sys.stderr)
        sys.exit(1)
    if not ok_a_ok:
        print("Expected: tx A accepted. Got above.", file=sys.stderr)
        sys.exit(1)

    print("PASS: B rejected, A accepted (sighash binding).")

    if dry_run:
        print("Dry-run: not broadcasting tx A.")
        return

    broadcast_txid = broadcast_or_raise(tx_a.hex)
    print("Broadcast tx A:", broadcast_txid)
    st = read_state(STATE_FILE)
    st.update(
        {
            "valid_spend_txid": broadcast_txid,
            "mutated_rejected": True,
        }
    )
    write_state(STATE_FILE, st)


def main() -> None:
    p = argparse.ArgumentParser(description="CHECKSIG sighash binding on Signet")
    p.add_argument("--fund", action="store_true", help="Fund the CHECKSIG tapscript address")
    p.add_argument("--demo", action="store_true", help="Run A/B mempool test + broadcast A")
    p.add_argument("--fee-sats", type=int, default=500)
    p.add_argument(
        "--delta-sats",
        type=int,
        default=100,
        help="Reduce output amount by this many sats for tx B vs A (default 100)",
    )
    p.add_argument("--dry-run", action="store_true", help="Do not broadcast tx A after checks")
    args = p.parse_args()
    wif = load_demo_wif()

    if args.fund:
        cmd_fund(wif)
    elif args.demo:
        cmd_demo(wif, args.fee_sats, args.delta_sats, args.dry_run)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
