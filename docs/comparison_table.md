# Binding target comparison

| Case | Binding target | Key source | Signed object | Replayable (same design) | What it shows |
|------|------------------|------------|---------------|---------------------------|---------------|
| **CSFS** | Message | Witness / stack | Arbitrary 32-byte message (or hashed payload) | Yes — same `(sig, msg, pubkey)` can satisfy multiple compatible script paths | Signature can be decoupled from a specific tx commitment |
| **IK + CSFS** | Identity (internal key) | Taproot context (`OP_INTERNALKEY`) | Message signed by that internal key | Yes — across UTXOs that share the same internal key | Adds *who* must have signed; still not automatic tx binding |
| **CHECKSIG** | Transaction | Locking / script path context | Sighash (tx digest) | No — same bytes reused against another tx/sighash fails | Signature is tied to the exact tx commitment being verified |

**Summary:** The main difference is not the signature algorithm, but **what the signature is verified against** (binding target).

**Further reading:** `docs/INTERPRETATION.md` explains each case and the JSON fields.
