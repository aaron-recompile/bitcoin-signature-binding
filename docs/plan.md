# Bitcoin Signature Binding Experiments Plan

## Goal

Compare three binding targets in Bitcoin script:

- **message** — `OP_CHECKSIGFROMSTACK` with stack-supplied pubkey
- **identity** — `OP_INTERNALKEY` + `OP_CHECKSIGFROMSTACK` (internal key as pubkey)
- **transaction** — `OP_CHECKSIG` / sighash commitment

## Cases

1. CSFS  
2. IK + CSFS  
3. CHECKSIG  

## Hypotheses

- CSFS binds signature validity to a **message**, not a specific transaction context.
- IK + CSFS binds validity to the **UTXO internal key identity**; it does not by itself bind to a unique transaction.
- CHECKSIG binds validity to a **transaction commitment** (Taproot sighash).
- **Replay** behavior follows from binding target, not from “having a signature” alone.

## Deliverables

- Executable `experiment.py` + per-case modules  
- Machine-readable results under `outputs/`  
- `comparison_table.md`  
- `README.md`  

## Interpretation boundaries

- Execution-level comparison; not a claim of new cryptography.
- Use **binding target** as the main abstraction.
- Do not claim IK+CSFS replaces CHECKSIG.
