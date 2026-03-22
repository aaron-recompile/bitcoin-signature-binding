# How to read this experiment: code, outputs, and conclusions

This document explains **what problem this experiment addresses**, **what each module does**, **what the JSON fields mean**, and **the conclusions in section 7**. It focuses on semantics and outputs, not step-by-step troubleshooting.

---

## 1. What problem does the experiment solve?

Core idea: **the signing algorithm can be Schnorr in all cases, but behavior differs depending on what the verifier aligns the signature with.**

We call that alignment target the **binding target**. Three script shapes:

| Name | What verification answers |
|------|---------------------------|
| **CSFS (pubkey on the stack)** | Whether someone signed **a specific 32-byte message** |
| **IK+CSFS** | Whether **the identity represented by this Taproot internal key** signed a message |
| **CHECKSIG (Tapscript)** | Whether someone signed **the sighash computed for this transaction** |

The code uses the same cryptographic tools and repeatable scripts/models to **freeze** the behavioral differences in `binding/outputs/*.json` for reproducibility and citation.

---

## 2. Entry point: what `experiment.py` does

1. **Calls** three modules in order: `csfs_case` → `ik_csfs_case` → `checksig_case`  
2. Writes each case’s full result to **`binding/outputs/<case>/case.json`**  
3. Writes **`binding/outputs/comparison/summary.json`**  
4. **Asserts** the planned contrasts (e.g. CSFS must both “reuse” and “fail on tampered message / wrong pubkey”)

If the run ends with three `[PASS]` lines, all assertions passed: **the implementation matches the intended comparison.**

---

## 3. Case A: `csfs_case.py` — message binding and reuse

**What it does**

- Uses a standard CSFS leaf (`OP_CHECKSIGFROMSTACK`; in this repo `RawScript("cc")`) — witness **`[sig, message, pubkey]`**; pubkey is **supplied by the spender**.  
- With a fixed message and fixed signing key, computes `sig`, then builds **two distinct synthetic spends** (e.g. different `prev_txid`) using the **same witness stack**.  
- At the crypto layer: tamper the message, or use **another valid x-only pubkey** (not random bit flips, to avoid invalid curve points) and re-verify.

**Why it matters**

- CSFS is essentially: **Verify(pub, msg, sig)**.  
- When the script only checks that equation, **changing UTXO / changing a tx** does not automatically change “the message” — the same **(sig, msg, pub)** can still hold across multiple spends that are **script-compatible**.  
- **`reuse_passes_for_csfs: true`** means: under **message-only** binding, **reuse can appear**.  
- **`mutations_fail: true`** means: wrong message or wrong pubkey fails verification — **not everything passes**, binding is to **message + correct pubkey**.

---

## 4. Case B: `ik_csfs_case.py` — identity binding and replay under the same key

**What it does**

- Abstracts **IK+CSFS** as: at verification, **pubkey must be the x-only `P` for the internal key** (not a full TapTree spend here — same Schnorr equation).  
- Sub-experiments: correct identity passes; wrong signer fails; two verifications under the same `P` pass (two UTXO “slots”); changing internal key fails.  
- Also outputs **`cbcc`** script hex; on-chain shape is **`OP_INTERNALKEY` + `OP_CHECKSIGFROMSTACK`**.

**Why it matters**

- The difference from CSFS is **not the algorithm** but **where pubkey comes from**: witness vs UTXO internal-key context.  
- **`identity_binding_holds: true`**: wrong-key signature / wrong-identity verify fails — **“who signed” binds to internal key**.  
- **`replay_same_key: true`**: if several UTXOs **share the same internal key**, the same **(sig, msg)** can still verify — **identity binding ≠ single-tx binding** and does **not** automatically prevent replay.

---

## 5. Case C: `checksig_case.py` — transaction / sighash binding

**What it does**

- Uses the vendored **`binding.vendor.taproot_checksig.checksig_raw`** harness (Taproot script-path sighash + verify).  
- Wraps output in a uniform JSON: **`binding_target: transaction`**, signature is over **sighash**, not an arbitrary stack message.  
- Same signature, **change output amount** → new sighash → **old sig fails** on the new sighash.

**Why it matters**

- On the CHECKSIG path, the “message” fed to Schnorr is the **protocol-defined sighash**, which **changes with the transaction**.  
- **`reuse_fails_for_checksig: true`** and **`sighash_changed: true`** mean: **you cannot move a signature for tx A onto tx B and expect it to verify**.

---

## 6. How to read `binding/outputs/`

| File | How to read it |
|------|----------------|
| **`binding/outputs/csfs/case.json`** | `binding_target`, `checks`, `subexperiments` (A1/A2/A3); `artifacts` has synthetic txs and witness template. |
| **`binding/outputs/ik_csfs/case.json`** | `checks.identity_binding_holds`, `replay_same_key`; `subexperiments` B1–B4. |
| **`binding/outputs/checksig/case.json`** | `binding_target: transaction`; two sighashes in `subexperiments`; `raw` is the full harness output. |
| **`binding/outputs/comparison/summary.json`** | Summary: binding flags per case and `main_observation`. |

When three `[PASS]` lines match the `checks` fields in JSON, **the run matches the intended comparison**.

---

## 7. Stable conclusions

1. **We are not comparing “whether there is a signature”** but **what the signature is aligned with in the verify equation**: message, identity (internal key), or transaction digest.  
2. **Whether replay is a problem** depends on what you want to bind: for message-only or identity-only binding, **reuse across UTXOs** can be a **normal mathematical outcome**; to bind **a single spend**, you need **sighash-style binding** or **encode tx/output uniqueness explicitly in the message**.  
3. **IK+CSFS** answers **“who” authorized**, not automatically **“only this one tx”** — that’s **CHECKSIG** or **message design**.

---

## Other docs in this repo

- **`README.md`**: how to run, layout, index of `docs/`.  
- **`comparison_table.md`**: one-page comparison table.  
- **`plan.md`**: goals and scope (short).  
- **`SIGNET_RESULTS.md`**: optional on-chain anchor notes (Signet).  
- **`anchors_recorded.json`**: machine-readable txids for those anchors.
