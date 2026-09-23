"""Fork replacements for upstream's exact-byte SHA-256 signing fixtures."""

import base64
import pytest
from .test_psbt import tdata
from .pages.home_pages.test_home import create_ctx


def wallet_for(data, kind):
    from embit.networks import NETWORKS
    from krux.key import Key, TYPE_SINGLESIG, TYPE_MULTISIG, TYPE_MINISCRIPT
    from krux.wallet import Wallet

    multisig = kind in ("P2SH", "P2WSH", "P2SH_P2WSH")
    policy = TYPE_MULTISIG if multisig else TYPE_SINGLESIG
    if kind == "MINIS_P2WSH":
        policy = TYPE_MINISCRIPT
    return Wallet(Key(data.TEST_MNEMONIC, policy, NETWORKS["test"]))


@pytest.mark.parametrize(
    "kind",
    [
        "P2PKH",
        "P2SH",
        "P2WPKH",
        "P2SH_P2WPKH",
        "P2WSH",
        "P2SH_P2WSH",
        "P2TR",
        "MINIS_P2WSH",
    ],
)
@pytest.mark.parametrize("trim", [False, True])
def test_application_signatures_and_exports(m5stickv, tdata, kind, trim):
    from embit import ec
    from embit.psbt import PSBT
    from krux.psbt import PSBTSigner
    from krux.qr import FORMAT_NONE

    wallet = wallet_for(tdata, kind)
    source = PSBT.parse(getattr(tdata, kind + "_PSBT"))
    for inp in source.inputs:
        inp.sighash_type = 0x21
    signer = PSBTSigner(wallet, source.serialize(), FORMAT_NONE)
    original = signer.psbt
    signer.sign(trim=trim)
    found = 0
    for i, inp in enumerate(original.inputs):
        digest = original.sighash(i, sighash=0x21)
        for pub, sig in inp.partial_sigs.items():
            assert sig[-1] == 0x21
            assert pub.verify(ec.Signature.parse(sig[:-1]), digest)
            assert not pub.verify(
                ec.Signature.parse(sig[:-1]), original.sighash(i, sighash=1)
            )
            found += 1
        if inp.taproot_key_sig:
            sig = inp.taproot_key_sig
            assert len(sig) == 65 and sig[-1] == 0x21
            pub = ec.PublicKey.from_xonly(inp.utxo.script_pubkey.data[2:])
            assert pub.schnorr_verify(ec.SchnorrSig.parse(sig[:-1]), digest)
            found += 1
    assert found > 0
    exported = PSBT.parse(signer.psbt.serialize())
    assert all(inp.sighash_type == 0x21 for inp in exported.inputs)
    serialized = signer.psbt.serialize()
    assert signer.psbt_qr()[0] == serialized


@pytest.mark.parametrize("encoding", ["raw", "base64", "ur"])
def test_unified_qr_encodings(m5stickv, tdata, encoding):
    from embit.psbt import PSBT
    from uUR import UR, Types
    from krux.psbt import PSBTSigner
    from krux.qr import FORMAT_NONE, FORMAT_PMOFN, FORMAT_UR

    p = PSBT.parse(tdata.P2WPKH_PSBT)
    for inp in p.inputs:
        inp.sighash_type = 0x21
    raw = p.serialize()
    data, fmt = raw, FORMAT_NONE
    if encoding == "base64":
        data, fmt = base64.b64encode(raw).decode(), FORMAT_PMOFN
    elif encoding == "ur":
        data, fmt = UR("crypto-psbt", Types.psbt_to_cbor(raw)), FORMAT_UR
    signer = PSBTSigner(wallet_for(tdata, "P2WPKH"), data, fmt)
    signer.sign()
    exported, out_fmt = signer.psbt_qr()
    assert out_fmt == fmt
    if encoding == "base64":
        exported = base64.b64decode(exported)
    elif encoding == "ur":
        exported = Types.psbt_from_cbor(exported.cbor)
    result = PSBT.parse(exported)
    assert all(inp.sighash_type == 0x21 for inp in result.inputs)
    assert all(
        sig[-1] == 0x21 for inp in result.inputs for sig in inp.partial_sigs.values()
    )


@pytest.mark.parametrize("mode", ["qr", "sd", "cancel", "reject", "high-fee"])
def test_home_chain_confirmation_and_export(mocker, m5stickv, tdata, mode):
    from embit.psbt import PSBT
    from krux.pages.home_pages.home import Home
    from krux.qr import FORMAT_NONE
    from krux.sd_card import SDHandler

    wallet = wallet_for(tdata, "P2WPKH")
    p = PSBT.parse(tdata.P2WPKH_PSBT)
    if mode != "reject":
        for inp in p.inputs:
            inp.sighash_type = 0x21
    ctx = create_ctx(mocker, [], wallet)
    home = Home(ctx)
    mocker.patch.object(
        home, "load_psbt", return_value=(p.serialize(), FORMAT_NONE, "")
    )
    mocker.patch.object(home, "_pre_load_psbt_warn", return_value=True)
    mocker.patch.object(home, "_post_load_psbt_warn", return_value=True)
    mocker.patch.object(home, "_unverified_amounts_psbt_warn", return_value=True)
    mocker.patch.object(home, "_fees_psbt_warn", return_value=mode != "high-fee")
    review = mocker.patch.object(home, "_display_transaction_for_review")
    mocker.patch.object(home, "prompt", return_value=mode != "cancel")
    qr = mocker.patch.object(home, "display_qr_codes")
    mocker.patch("krux.pages.utils.Utils.print_standard_qr")
    menu = mocker.patch("krux.pages.home_pages.home.Menu").return_value
    menu.back_index = 3
    menu.run_loop.return_value = (2 if mode == "sd" else 1, None)
    mocker.patch.object(home, "_format_psbt_file_extension", return_value="signed.psbt")
    mocker.patch.object(home, "has_sd_card", return_value=True)
    sd = mocker.patch.object(SDHandler, "__enter__", return_value=mocker.MagicMock())
    mocker.patch.object(SDHandler, "__exit__", return_value=False)
    opened = mocker.patch("builtins.open", mocker.mock_open())
    opened().write.side_effect = len
    sign = mocker.spy(PSBT, "sign_with")
    if mode == "reject":
        with pytest.raises(ValueError, match="requires explicit unified"):
            home.sign_psbt()
    else:
        home.sign_psbt()
        ctx.display.draw_centered_text.assert_any_call(
            "BLAKE2b chain only\nUnified SIGHASH_ALL (0x21)"
        )
    if mode in ("cancel", "reject", "high-fee"):
        sign.assert_not_called()
        qr.assert_not_called()
        review.assert_not_called()
        return
    review.assert_called_once()
    assert sign.call_args.kwargs["sighash"] == 0x21
    if mode == "qr":
        exported = base64.b64decode(qr.call_args.args[0])
    else:
        qr.assert_not_called()
        exported = b"".join(c.args[0] for c in opened().write.call_args_list)
    signed = PSBT.parse(exported)
    assert all(inp.sighash_type == 0x21 for inp in signed.inputs)
    assert all(
        sig[-1] == 0x21 for inp in signed.inputs for sig in inp.partial_sigs.values()
    )
