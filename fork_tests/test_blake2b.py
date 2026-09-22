"""Actual signatures, strict negotiation, and hostile PSBT regression tests."""

import pytest
from embit import bip32, ec, script
from embit.psbt import PSBT, DerivationPath
from embit.transaction import Transaction, TransactionInput, TransactionOutput
from krux.blake2b import UNIFIED_ALL, check_psbt, sign_psbt, _check_script

ROOT = bip32.HDKey.from_seed(bytes(range(32)))
PATH = "m/84h/0h/0h/0/0"
CHILD = ROOT.derive(PATH)
PUB = CHILD.get_public_key()


def make_psbt(kind="p2wpkh", count=1):
    redeem = None
    witness = None
    if kind == "p2tr":
        spk = script.p2tr(PUB)
    elif kind == "p2pkh":
        spk = script.p2pkh(PUB)
    elif kind in ("p2wsh", "p2sh-p2wsh", "p2sh"):
        multisig = script.multisig(1, [PUB])
        if kind == "p2sh":
            redeem = multisig
            spk = script.p2sh(redeem)
        else:
            witness = multisig
            spk = script.p2wsh(witness)
            if kind == "p2sh-p2wsh":
                redeem = spk
                spk = script.p2sh(redeem)
    else:
        spk = script.p2wpkh(PUB)
        if kind == "p2sh-p2wpkh":
            redeem = spk
            spk = script.p2sh(redeem)
    prev = Transaction(
        vin=[TransactionInput(b"\x11" * 32, 0)],
        vout=[TransactionOutput(100000, spk) for _ in range(count)],
    )
    p = PSBT(
        Transaction(
            vin=[TransactionInput(prev.txid(), i) for i in range(count)],
            vout=[TransactionOutput(count * 90000, script.p2wpkh(PUB))],
        )
    )
    for i, inp in enumerate(p.inputs):
        inp.sighash_type = UNIFIED_ALL
        inp.redeem_script = redeem
        inp.witness_script = witness
        if kind in ("p2pkh", "p2sh"):
            inp.non_witness_utxo = prev
        else:
            inp.witness_utxo = prev.vout[i]
        path = DerivationPath(ROOT.my_fingerprint, bip32.parse_path(PATH))
        if kind == "p2tr":
            inp.taproot_internal_key = PUB
            inp.taproot_bip32_derivations[PUB] = ([], path)
        else:
            inp.bip32_derivations[PUB] = path
    return p


@pytest.mark.parametrize(
    "kind", ["p2pkh", "p2sh", "p2wpkh", "p2sh-p2wpkh", "p2wsh", "p2sh-p2wsh", "p2tr"]
)
def test_real_signatures_only_verify_unified(kind):
    p = make_psbt(kind, 2)
    assert sign_psbt(p, ROOT) == 2
    for i, inp in enumerate(p.inputs):
        unified = p.sighash(i, sighash=0x21)
        standard = p.sighash(i, sighash=1)
        old_algorithm_same_byte = (
            p.tx.sighash_taproot(
                i,
                [x.utxo.script_pubkey for x in p.inputs],
                [x.utxo.value for x in p.inputs],
                sighash=1,
            )
            if kind == "p2tr"
            else None
        )
        if kind == "p2tr":
            sig = inp.taproot_key_sig
            assert len(sig) == 65 and sig[-1] == 0x21
            verifier = ec.PublicKey.from_xonly(inp.utxo.script_pubkey.data[2:])
            parsed = ec.SchnorrSig.parse(sig[:-1])
            assert verifier.schnorr_verify(parsed, unified)
            assert not verifier.schnorr_verify(parsed, standard)
            assert not verifier.schnorr_verify(parsed, old_algorithm_same_byte)
        else:
            sig = inp.partial_sigs[PUB]
            assert sig[-1] == 0x21
            parsed = ec.Signature.parse(sig[:-1])
            assert PUB.verify(parsed, unified)
            assert not PUB.verify(parsed, standard)
        # Every amount is committed, including the sibling input's amount.
        sibling = p.inputs[1 - i].utxo
        sibling.value += 1
        assert p.sighash(i, sighash=0x21) != unified
        sibling.value -= 1


@pytest.mark.parametrize(
    "requested", [None] + [i for i in range(256) if i != 0x21] + [0x121, -1]
)
def test_every_other_sighash_rejected_before_any_signature(requested):
    p = make_psbt(count=2)
    p.inputs[1].sighash_type = requested
    with pytest.raises(ValueError, match="Input 1 requires"):
        sign_psbt(p, ROOT)
    assert not p.inputs[0].partial_sigs


@pytest.mark.parametrize(
    "mutation,match",
    [
        (lambda p: setattr(p.inputs[1], "witness_utxo", None), "Every input"),
        (lambda p: setattr(p.inputs[1], "vout", 0), "Duplicate"),
        (lambda p: setattr(p.inputs[1].utxo, "value", -1), "Every input"),
        (lambda p: setattr(p.outputs[0], "value", 300000), "amounts"),
        (
            lambda p: setattr(
                p.outputs[0], "script_pubkey", script.Script(b"\x51" * 35)
            ),
            "Output script",
        ),
        (
            lambda p: setattr(
                p.outputs[0], "script_pubkey", script.Script(b"\x6a" + b"x" * 83)
            ),
            "Output script",
        ),
        (
            lambda p: p.inputs[1].partial_sigs.update({PUB: b"bad\x01"}),
            "Existing signatures",
        ),
        (
            lambda p: setattr(
                p.inputs[1], "final_scriptwitness", script.Witness([b"bad"])
            ),
            "Finalized",
        ),
    ],
)
def test_invalid_psbt_fails_before_signing(mutation, match):
    p = make_psbt(count=2)
    mutation(p)
    with pytest.raises(ValueError, match=match):
        sign_psbt(p, ROOT)
    assert not p.inputs[0].partial_sigs


def test_legacy_witness_hint_cannot_change_digest_domain():
    p = make_psbt("p2pkh")
    p.inputs[0].witness_utxo = p.inputs[0].utxo
    with pytest.raises(ValueError, match="Legacy inputs"):
        sign_psbt(p, ROOT)


@pytest.mark.parametrize(
    "raw,match",
    [
        (b"\x63", "OP_IF"),
        (b"\x64", "OP_IF"),
        (b"\xab", "CODESEPARATOR"),
        (b"\x4d\x01\x01" + b"x" * 257, "256"),
        (b"\x4d", "Truncated"),
    ],
)
def test_rdts_script_restrictions(raw, match):
    with pytest.raises(ValueError, match=match):
        _check_script(raw, tapscript=True)


def test_opcode_bytes_in_push_are_not_opcodes():
    _check_script(b"\x03\x63\x64\xab", tapscript=True)


def test_output_script_boundaries():
    p = make_psbt()
    for raw in (b"\x51" * 34, b"\x6a" + b"x" * 82):
        p.outputs[0].script_pubkey = script.Script(raw)
        check_psbt(p)


def test_psbt_roundtrip_preserves_explicit_opt_in():
    p = make_psbt()
    restored = PSBT.parse(p.serialize())
    assert restored.inputs[0].sighash_type == 0x21
    assert sign_psbt(restored, ROOT) == 1
