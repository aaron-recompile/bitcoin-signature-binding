"""Replay slice for Case B (IK+CSFS). Full data in `ik_csfs_case.run_ik_csfs_case`."""

from __future__ import annotations

import json

from binding.ik_csfs_case import run_ik_csfs_case

if __name__ == "__main__":
    r = run_ik_csfs_case()
    print(
        json.dumps(
            {
                "B3_replay": r["subexperiments"]["B3_replay_same_key_utxos"],
                "B4_other_identity": r["subexperiments"]["B4_different_internal_key"],
                "checks": r["checks"],
            },
            indent=2,
        )
    )
