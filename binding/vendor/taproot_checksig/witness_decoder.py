from typing import Dict


def decode_tapscript_checksig(script_hex: str) -> Dict[str, str]:
    script = bytes.fromhex(script_hex)
    if len(script) < 34:
        raise ValueError("Tapscript too short for <pubkey> OP_CHECKSIG pattern")
    if script[0] != 0x20:
        raise ValueError("Expected OP_PUSHBYTES_32 at script start")
    pubkey_xonly = script[1:33].hex()
    opcode = script[33]
    return {
        "pubkey_xonly": pubkey_xonly,
        "opcode_hex": f"{opcode:02x}",
        "is_op_checksig": opcode == 0xAC,
    }


def decode_witness_stack(witness_stack) -> Dict[str, object]:
    if len(witness_stack) < 3:
        raise ValueError("Expected witness stack with [signature, tapscript, control_block]")

    first_item = bytes.fromhex(witness_stack[0])
    annex_present = bool(first_item) and first_item[0] == 0x50

    return {
        "signature": witness_stack[0],
        "tapscript": witness_stack[-2],
        "control_block": witness_stack[-1],
        "stack_items_count": len(witness_stack),
        "annex_present": annex_present,
    }
