# Signet anchors (optional)

These scripts are **incremental** to the offline comparison in `binding.experiment`. They do **not** replace the JSON/assert workflow; they add **chain-visible** evidence for:

| Script | Story |
|--------|--------|
| `replay_csfs.py` | Two **funds** to the same CSFS leaf, two **spends** with the **same** `[sig, message, pubkey]` witness. |
| `replay_ik_csfs.py` | Same for **IK+CSFS** (`OP_INTERNALKEY` + `OP_CHECKSIGFROMSTACK`), same `[sig, message]`. |
| `sighash_checksig.py` | **Valid** Tapscript `OP_CHECKSIG` spend (tx A). Tx **B** = clone of A with a **different output amount** but **same witness** → `testmempoolaccept` **rejects** B; then broadcast A. |

## Requirements

- `binding.rpc_config` (`INQUISITION_DATADIR`, …), **`INQUISITION_RPC_WALLET`** (must match a wallet loaded on your node; see `rpc_config.rpc_wallet`), **`BINDING_DEMO_WIF`** (Signet key).
- **`.env` (recommended):** from repo root run `cp env.example .env` and set `BINDING_DEMO_WIF` and `INQUISITION_DATADIR`. Scripts load this on startup (`binding/signet/_common.py`); shell `export` is optional.
- Run with **`PYTHONPATH=.`** from this repo root so `binding` resolves.

## Commands (from repo root `bitcoin-signature-binding/`)

```bash
export PYTHONPATH=.
export BINDING_DEMO_WIF="..."
export INQUISITION_DATADIR="..."

# CSFS replay
python -m binding.signet.replay_csfs --fund-twice
python -m binding.signet.replay_csfs --spend --input-txid <first_fund_txid>
python -m binding.signet.replay_csfs --spend --input-txid <second_fund_txid>

# IK+CSFS replay
python -m binding.signet.replay_ik_csfs --fund-twice
python -m binding.signet.replay_ik_csfs --spend --input-txid <...>

# CHECKSIG sighash binding
python -m binding.signet.sighash_checksig --fund
python -m binding.signet.sighash_checksig --demo
# optional: --dry-run to only run testmempoolaccept without broadcasting A
```

Messages are `SHA256("binding-exp-msg:csfs")` and `SHA256("binding-exp-msg:ik_csfs")` to match `csfs_case.py` / `ik_csfs_case.py`.

## Artifacts

- JSON state files next to these modules: `state_replay_csfs.json`, `state_replay_ik_csfs.json`, `state_sighash_checksig.json` (see `.gitignore`).
- Copy txids into `docs/anchors.template.json` if you maintain a fixed anchor list.

After a successful run, you can record txids in **`docs/SIGNET_RESULTS.md`** and **`docs/anchors_recorded.json`**.
