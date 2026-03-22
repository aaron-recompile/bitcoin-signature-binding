"""Replay slice for Case A (CSFS). Full data in `csfs_case.run_csfs_case`."""

from __future__ import annotations

import json

from binding.csfs_case import run_csfs_case

if __name__ == "__main__":
    r = run_csfs_case()
    print(
        json.dumps(
            {
                "A2_reuse": r["subexperiments"]["A2_reuse_same_sig_msg_pubkey"],
                "checks": r["checks"],
            },
            indent=2,
        )
    )
