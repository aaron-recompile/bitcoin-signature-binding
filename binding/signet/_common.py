"""
Shared helpers for binding Signet demos (replay CSFS / IK+CSFS / CHECKSIG sighash).

Requires repo root on PYTHONPATH (`PYTHONPATH=.` from repo root), `binding.rpc_config`,
`btcaaron`, and **`BINDING_DEMO_WIF`** (Signet demo key).

Environment: optional `.env` in repo root or `binding/` (see `env.example`).
Loaded on import; existing shell variables are not overwritten.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

from btcaaron.node_rpc import sats_from_rpc_amount

# Same message bytes as offline `csfs_case.py` / `ik_csfs_case.py`.
MESSAGE_CSFS = hashlib.sha256(b"binding-exp-msg:csfs").digest()
MESSAGE_IK_CSFS = hashlib.sha256(b"binding-exp-msg:ik_csfs").digest()

Utxo = Tuple[str, int, int]  # txid, vout, sats

SIGNET_DIR = Path(__file__).resolve().parent
_BINDING_ROOT = Path(__file__).resolve().parents[1]  # binding/
_REPO_ROOT = Path(__file__).resolve().parents[2]  # bitcoin-signature-binding/


def _load_dotenv_files() -> None:
    """Parse KEY=VALUE from `.env` files; only set keys that are not already in os.environ."""
    for env_path in (_BINDING_ROOT / ".env", _REPO_ROOT / ".env"):
        if not env_path.is_file():
            continue
        try:
            text = env_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            if not key:
                continue
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val


_load_dotenv_files()


def load_demo_wif() -> str:
    wif = os.environ.get("BINDING_DEMO_WIF", "").strip()
    if not wif:
        raise ValueError(
            "Set BINDING_DEMO_WIF (Signet demo key; e.g. in repo `.env` — see env.example), "
            "or export it in the shell."
        )
    return wif


def utxo_from_funding_txid(address: str, txid: str) -> Optional[Utxo]:
    """
    Find (txid, vout, sats) for an output paying to `address` in `txid`.

    Uses `getrawtransaction` so **unconfirmed** fund txs work; `scantxoutset` often misses those.
    """
    from binding.rpc_config import rpc

    try:
        raw = rpc("getrawtransaction", txid, True)
    except Exception:
        return None
    if not raw:
        return None
    for out in raw.get("vout", []):
        spk = out.get("scriptPubKey", {})
        if spk.get("address") != address:
            continue
        n = int(out["n"])
        val = out.get("value")
        if val is None:
            continue
        return (txid, n, sats_from_rpc_amount(val))
    return None


def list_utxos_for_address(address: str) -> List[Utxo]:
    """All UTXOs paying to `address` via scantxoutset (best-effort)."""
    from binding.rpc_config import rpc

    try:
        rpc("scantxoutset", "abort")
    except Exception:
        pass
    scan = rpc("scantxoutset", "start", json.dumps([f"addr({address})"]))
    unspents = scan.get("unspents", [])
    out: List[Utxo] = []
    for u in unspents:
        amt = u.get("value", u.get("amount"))
        if amt is None:
            continue
        out.append((u["txid"], int(u["vout"]), sats_from_rpc_amount(amt)))
    return out


def read_state(name: str) -> dict[str, Any]:
    p = SIGNET_DIR / name
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write_state(name: str, data: dict[str, Any]) -> None:
    p = SIGNET_DIR / name
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote state: {p}")
