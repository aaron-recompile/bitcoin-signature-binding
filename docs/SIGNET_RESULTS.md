# Signet anchor record (Bitcoin Inquisition Signet)

**Network:** Bitcoin Inquisition Signet (`INQUISITION_DATADIR` + RPC). On-chain behavior should match the offline `python -m binding.experiment` model and `docs/INTERPRETATION.md`.  
**Recorded:** 2026-03-21 (execution order as run)  
**Explorer:** `https://mempool.space/signet/tx/<TXID>`

---

## 1. CSFS — two funds, two spends (same witness `[sig, message, pubkey]`)

| Step | txid |
|------|------|
| Fund #1 | `634a3a0c55c70258298e5a5880991190c651f14843b9b8b5ca106a554cbd5a9e` |
| Fund #2 | `13b2d60335c399ef3209e14283241c1913385a08280cc048517c3e577f664879` |
| Reveal #1 | `40b38a204e17a8198aa349cf52cafcaa3c11e16bb7aeabf7a034e48f432f3ea4` |
| Reveal #2 | `7f57ac73b0e6fb394e735ced500af78abfddb57737df3f4a002b3e8ed7ffeeb9` |

**MESSAGE (off-chain):** `SHA256("binding-exp-msg:csfs")` (same as `csfs_case.py`)

**Note:** Both funds pay to the same P2TR+CSFS lock; both reveals use the **same** witness stack and differ only in `prevout`. Under **message-level** binding, replay across distinct UTXOs is allowed by the script — it is **not** double-spending the same coin.

---

## 2. IK+CSFS — two funds, two spends (same witness `[sig, message]`)

| Step | txid |
|------|------|
| Fund #1 | `9f37cab42100bdf738d06f45814a7d3a77ef919b958195b7192d460e63dafdff` |
| Fund #2 | `dcf8a98522b8ffa46194abf45fc8c227696cba58b4741f27dd6f2ddf4d461206` |
| Reveal #1 | `34222f1fa6b28b190e59baaf64b57e25755b174ffe50422f06893e5ce196624b` |
| Reveal #2 | `2a4eb8619af7fbcfdd39ef62c128ba8b60382a0929040210bbbeaec31aa62f5f` |

**MESSAGE:** `SHA256("binding-exp-msg:ik_csfs")` (same as `ik_csfs_case.py`)

**Note:** Pubkey context comes from the **internal key** (`OP_INTERNALKEY` + `OP_CHECKSIGFROMSTACK`). The same `(sig, msg)` can unlock two UTXOs that share that internal key — **identity-level** binding still does not imply “authorization for exactly one specific transaction.”

**Implementation:** Unconfirmed fund outputs may be missed by `scantxoutset`; scripts also resolve UTXOs via `getrawtransaction` (`utxo_from_funding_txid`).

---

## 3. CHECKSIG (Tapscript) — sighash binding: mutated tx rejected, valid tx broadcast

| Field | Value |
|------|-------|
| Fund (to `<xonly> OP_CHECKSIG` script path) | `96b1a474c6909b1c4e4ef7883b51e3440753035902117ce0816870bea36e1494` |
| P2TR address | `tb1ppyks5dy00fcjjcfxh7a8ndm2qhvwz5l82wmzykc7nyffgg6sapnq7w6xfr` |
| **Tx A** (valid script-path spend, `testmempoolaccept` allowed) | `5225349237a3e6240b84d2c68095b0d232cbdf05367fe02d5dee191ea777a18f` |
| **Tx B** (clone of A with different output amount, reuses A’s witness; **not broadcast**) | `cc9ebd50dd81f20834b687e94aa745c16c1cdeab14d739450793499d484457b6` (only used for `testmempoolaccept`) |

**`testmempoolaccept` response for Tx B (typical shape; single element in array):**

```json
[
  {
    "txid": "cc9ebd50dd81f20834b687e94aa745c16c1cdeab14d739450793499d484457b6",
    "allowed": false,
    "reject-reason": "mempool-script-verify-flag-failed (Invalid Schnorr signature)"
  }
]
```

(Field names may differ slightly by node version; the important parts are `allowed: false` and `Invalid Schnorr signature`.)

**Note:** On the Tapscript `OP_CHECKSIG` path the signature commits to **sighash(this transaction)**. Changing the output changes the sighash, so the original signature does **not** verify for the modified transaction. This matches offline `checksig_case` / `binding.vendor.taproot_checksig`.

---

## 4. One-line map to offline `experiment.py`

| Offline `binding_target` | What Signet demonstrates |
|--------------------------|---------------------------|
| message (CSFS) | Two different prevouts; same witness can spend twice |
| identity (IK+CSFS) | Same; `[sig, msg]` bound to internal key |
| transaction (CHECKSIG) | Same signature bytes cannot be moved to an altered tx; valid spend broadcasts |

---

## 5. Machine-readable summary

See **`docs/anchors_recorded.json`** (same directory as this file; txids only, no keys).
