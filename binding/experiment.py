"""
Run all three binding cases and write outputs + summary.

  PYTHONPATH=. python -m binding.experiment
"""

from __future__ import annotations

import json
from pathlib import Path

from .checksig_case import run_checksig_case
from .csfs_case import run_csfs_case
from .ik_csfs_case import run_ik_csfs_case

OUT = Path(__file__).resolve().parent / "outputs"


def _write_json(rel: str, data: object) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_comparison(csfs: dict, ik: dict, chk: dict) -> dict:
    return {
        "main_observation": (
            "Replay behavior follows binding target: message-bound and identity-bound "
            "signatures can replay where script allows; sighash-bound signatures do not "
            "survive tx mutation."
        ),
        "cases": {
            "CSFS": {
                "binding_target": csfs["binding_target"],
                "replayable": csfs["replayable"],
                "checks": csfs.get("checks"),
            },
            "IK+CSFS": {
                "binding_target": ik["binding_target"],
                "replayable_across_same_internal_key": ik["replayable_across_same_internal_key"],
                "checks": ik.get("checks"),
            },
            "CHECKSIG": {
                "binding_target": chk["binding_target"],
                "replayable": chk["replayable"],
                "checks": chk.get("checks"),
            },
        },
    }


def run() -> None:
    csfs = run_csfs_case()
    ik = run_ik_csfs_case()
    chk = run_checksig_case()
    summary = _write_comparison(csfs, ik, chk)

    _write_json("csfs/case.json", csfs)
    _write_json("ik_csfs/case.json", ik)
    _write_json("checksig/case.json", chk)
    _write_json("comparison/summary.json", summary)

    assert csfs["checks"]["reuse_passes_for_csfs"], "CSFS reuse demo failed"
    assert csfs["checks"]["mutations_fail"], "CSFS mutation demo failed"
    assert ik["checks"]["identity_binding_holds"], "IK+CSFS identity checks failed"
    assert ik["checks"]["replay_same_key"], "IK+CSFS replay demo failed"
    assert chk["checks"]["reuse_fails_for_checksig"], "CHECKSIG contrast failed"
    assert chk["checks"]["sighash_changed"], "CHECKSIG sighash change not detected"

    print("[PASS] CSFS:", csfs["checks"])
    print("[PASS] IK+CSFS:", ik["checks"])
    print("[PASS] CHECKSIG:", {k: chk["checks"][k] for k in ("reuse_fails_for_checksig", "sighash_changed")})
    print("Wrote:", OUT)


if __name__ == "__main__":
    run()
