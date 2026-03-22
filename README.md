# bitcoin-signature-binding

**Reference code and reproducible outputs** for a **Delving Bitcoin** discussion of **what Schnorr signatures are verified against** in Bitcoin Tapscript: **CSFS** (message + pubkey on the stack), **internal key + CSFS** (identity from the UTXO), and **CHECKSIG** (transaction sighash).

The repository is **self-contained**: runnable harnesses, checked-in **`binding/outputs/`** JSON (regenerate with `python -m binding.experiment` and compare), and documentation under `docs/`.

**Expectations:** (1) **Offline / math layer** — only Python deps and `PYTHONPATH`; no blockchain RPC. (2) **Signet** — optional scripts under `binding/signet/`; require a Signet node, `btcaaron`, and `.env` as in `env.example`.

## Layout

| Path | Purpose |
|------|---------|
| `binding/experiment.py` | Run all three cases, write `binding/outputs/` JSON |
| `binding/csfs_case.py`, `ik_csfs_case.py`, `checksig_case.py` | Case logic |
| `binding/rpc_config.py` | Signet RPC (`bitcoin-cli -signet`, `INQUISITION_DATADIR`, …) |
| `binding/template_common.py` | Fund/spend helpers for Signet demos |
| `binding/vendor/inquisition_opcodes.py` | Opcode helpers (`OP_INTERNALKEY`, `OP_CHECKSIGFROMSTACK`, `build_script`) for Bitcoin Inquisition–style tapscript |
| `binding/vendor/taproot_checksig/` | Minimal CHECKSIG / sighash trace (self-contained under `binding/`) |
| `binding/signet/` | On-chain demos: replay CSFS / IK+CSFS, CHECKSIG sighash |
| `docs/` | See [`docs/README.md`](docs/README.md); `INTERPRETATION.md`, `comparison_table.md`, `SIGNET_RESULTS.md`, `anchors_recorded.json` |

## Setup

```bash
cd bitcoin-signature-binding
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # only needed for Signet scripts; see env.example
```

Uses **`btcaaron` from PyPI** (and **`secp256k1`**) together with:

- **CSFS leaf** as `RawScript("cc")` (`OP_CHECKSIGFROMSTACK`). Equivalent to `inq_csfs_script()` where that helper exists in your `btcaaron` build.
- **CHECKSIG harness** (`binding/vendor/taproot_checksig/tx_builder.py`) derives unsigned tx metadata via `to_bytes(False)` instead of `SpendBuilder.to_psbt()` (some `btcaaron` releases omit PSBT helpers).

## Offline run (no `bitcoind`)

```bash
export PYTHONPATH=.
python -m binding.experiment
```

This writes JSON under `binding/outputs/` and should match the checked-in reference outputs for the same dependency versions.

Optional JSON-only slices:

```bash
python -m binding.replay_demo_csfs
python -m binding.replay_demo_ik_csfs
```

## Signet (optional)

See **`binding/signet/README.md`**. Requires a **Bitcoin Inquisition** Signet `bitcoind` (or compatible) with RPC enabled, a **wallet name** matching `INQUISITION_RPC_WALLET` in `.env`, `btcaaron`, and the rest of **`env.example`**.

## License

Code in this repository is released under the **MIT License** — see [`LICENSE`](LICENSE).

Python dependencies (`btcaaron`, `secp256k1`, etc.) are subject to their respective licenses. Vendored code under `binding/vendor/` is included for reproducibility; see per-file comments where applicable.
