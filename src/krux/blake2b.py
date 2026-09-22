# SPDX-License-Identifier: MIT
"""Fail-closed signing policy for the Knots BLAKE2b fork.

Consensus reference: v29.4.2.knots20260508. This offline policy cannot
determine activation, UTXO existence, maturity, or the current chain tip.
RDTS restrictions are deliberately retained even after their scheduled expiry.
"""

from embit.transaction import SIGHASH

UNIFIED_ALL = 0x21
MAX_MONEY = 21000000 * 100000000
RDTS_BLOCK_WEIGHT = 800000


def _check_script(data, tapscript=False):
    """Walk opcodes, not bytes inside pushes; no code-separator support."""
    pos = 0
    while pos < len(data):
        opcode = data[pos]
        pos += 1
        if opcode == 0xAB:
            raise ValueError("OP_CODESEPARATOR signing is unsupported")
        if tapscript and opcode in (0x63, 0x64):
            raise ValueError("RDTS forbids OP_IF/OP_NOTIF in tapscript")
        size = 0
        if 1 <= opcode <= 75:
            size = opcode
        elif opcode in (76, 77, 78):
            width = 1 << (opcode - 76)
            if pos + width > len(data):
                raise ValueError("Truncated script push")
            size = int.from_bytes(data[pos : pos + width], "little")
            pos += width
        if size > 256:
            raise ValueError("RDTS script element exceeds 256 bytes")
        if pos + size > len(data):
            raise ValueError("Truncated script push")
        pos += size


def check_psbt(psbt):
    """Validate every input before any key signs; never upgrade a request."""
    if getattr(SIGHASH, "UNIFIED", None) != 0x20:
        raise ValueError("Unified sighash dependency is missing")
    if not psbt.inputs or not psbt.outputs:
        raise ValueError("Transaction needs inputs and outputs")
    seen = set()
    total_in = 0
    for index, inp in enumerate(psbt.inputs):
        if inp.sighash_type != UNIFIED_ALL:
            raise ValueError(
                "Input %d requires explicit unified SIGHASH_ALL (0x21)" % index
            )
        if inp.final_scriptsig or inp.final_scriptwitness:
            raise ValueError(
                "Finalized inputs are unsupported; provide an unfinalized PSBT"
            )
        signatures = list(inp.partial_sigs.values()) + list(inp.taproot_sigs.values())
        if inp.taproot_key_sig:
            signatures.append(inp.taproot_key_sig)
        if any(not sig or sig[-1] != UNIFIED_ALL for sig in signatures):
            raise ValueError("Existing signatures must use unified SIGHASH_ALL")
        if inp.taproot_key_sig and len(inp.taproot_key_sig) != 65:
            raise ValueError("Unified taproot signature must be 65 bytes")
        if any(len(sig) != 65 for sig in inp.taproot_sigs.values()):
            raise ValueError("Unified tapscript signature must be 65 bytes")
        utxo = inp.utxo
        if utxo is None or not 0 <= utxo.value <= MAX_MONEY:
            raise ValueError("Every input needs a valid spent output and amount")
        total_in += utxo.value
        outpoint = (inp.txid, inp.vout)
        if outpoint in seen:
            raise ValueError("Duplicate transaction input")
        seen.add(outpoint)
        # embit uses witness_utxo presence when choosing the unified script type.
        # A legacy input must not be misclassified as witness-v0 by that hint.
        kind = utxo.script_pubkey.script_type()
        nested = inp.redeem_script and inp.redeem_script.script_type() in (
            "p2wpkh",
            "p2wsh",
        )
        if kind not in ("p2pkh", "p2sh", "p2wpkh", "p2wsh", "p2tr"):
            raise ValueError("Unsupported spent output type")
        if inp.witness_utxo and kind not in ("p2wpkh", "p2wsh", "p2tr") and not nested:
            raise ValueError("Legacy inputs must use non_witness_utxo only")
        for sc in (inp.redeem_script, inp.witness_script):
            if sc:
                _check_script(sc.data)
        for control, leaf in inp.taproot_scripts.items():
            if not 33 <= len(control) <= 257 or (len(control) - 33) % 32:
                raise ValueError(
                    "RDTS taproot control block exceeds seven nodes or is malformed"
                )
            if not leaf or leaf[-1] != 0xC0 or control[0] & 0xFE != 0xC0:
                raise ValueError("Unsupported tapleaf version")
            _check_script(leaf[:-1], tapscript=True)
    total_out = 0
    for out in psbt.outputs:
        if not 0 <= out.value <= MAX_MONEY:
            raise ValueError("Invalid output amount")
        total_out += out.value
        data = out.script_pubkey.data
        limit = 83 if data and data[0] == 0x6A else 34
        if len(data) > limit:
            raise ValueError("Output script exceeds RDTS limit")
    if total_in > MAX_MONEY or total_out > total_in:
        raise ValueError("Invalid transaction amounts")
    # An unsigned transaction already this large cannot fit into an RDTS block.
    # Actual signed weight and block overhead remain the node's responsibility.
    if len(psbt.tx.serialize()) * 4 >= RDTS_BLOCK_WEIGHT:
        raise ValueError("Transaction cannot fit in an RDTS block")


def sign_psbt(psbt, root):
    """The only transaction signing entry point in this fork."""
    check_psbt(psbt)
    psbt.verify(ignore_missing=True)
    return psbt.sign_with(root, sighash=UNIFIED_ALL)
