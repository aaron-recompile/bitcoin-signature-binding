"""
RPC helpers for `bitcoin-cli -signet` against a local Bitcoin Inquisition (or compatible) node.

Environment: `INQUISITION_DATADIR`, optional `INQUISITION_RPC_PORT`, `INQUISITION_RPC_WALLET`,
`BITCOIN_CLI`. See `env.example`.
"""
import json
import subprocess
import os

# RPC_DATADIR = "/path/to/inquisition-data"
# CLI_PATH = "bitcoin-cli"  # or full path to bitcoin-cli
RPC_DATADIR = os.environ.get("INQUISITION_DATADIR", "")
CLI_PATH = os.environ.get("BITCOIN_CLI", "bitcoin-cli")
RPC_PORT = os.environ.get("INQUISITION_RPC_PORT", "")  # e.g. 38335 if your node uses a non-default RPC port


def _check_config():
    if not RPC_DATADIR:
        raise ValueError(
            "Set INQUISITION_DATADIR (path to your Inquisition node datadir). "
            "Example: export INQUISITION_DATADIR=/path/to/inquisition-data"
        )


def _rpc_cmd_base():
    cmd = [CLI_PATH, "-signet", f"-datadir={RPC_DATADIR}"]
    if RPC_PORT:
        cmd.append(f"-rpcport={RPC_PORT}")
    return cmd


def rpc(method, *params):
    _check_config()
    cmd = _rpc_cmd_base() + [method]
    for p in params:
        if isinstance(p, (dict, list, bool, type(None))):
            cmd.append(json.dumps(p))
        else:
            cmd.append(str(p))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"RPC error: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()


def rpc_wallet(method, *params, wallet: str | None = None):
    _check_config()
    w = wallet if wallet is not None else os.environ.get("INQUISITION_RPC_WALLET", "lab")
    cmd = _rpc_cmd_base() + [f"-rpcwallet={w}", method]
    for p in params:
        if isinstance(p, (dict, list, bool, type(None))):
            cmd.append(json.dumps(p))
        else:
            cmd.append(str(p))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"RPC error: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return result.stdout.strip()
