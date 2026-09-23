"""Run real-node acceptance/replay checks with disposable regtest coins only.

Usage: PYTHONPATH=src python fork_tests/regtest.py /path/to/bitcoind
Requires Bitcoin Knots v29.4.2.knots20260508. Never connects to a user node.
"""

import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

from embit import hashes, script
from embit.finalizer import finalize_psbt
from embit.networks import NETWORKS
from embit.transaction import Transaction
from test_blake2b import ROOT, CHILD, PUB, make_psbt
from krux.blake2b import sign_psbt


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    token = base64.b64encode(b"regtest:disposable-local-test").decode()

    def rpc(method, *params):
        request = urllib.request.Request(
            "http://127.0.0.1:%d" % port,
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
            ).encode(),
            {"Authorization": "Basic " + token, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result["result"]

    process = None
    with tempfile.TemporaryDirectory(prefix="krux-blake2b-regtest-") as tmp:
        log = open(Path(tmp) / "console.log", "wb")

        def start(extra=()):
            nonlocal process
            args = [
                sys.argv[1],
                "-regtest",
                "-server",
                "-listen=0",
                "-discover=0",
                "-dnsseed=0",
                "-rpcbind=127.0.0.1",
                "-rpcallowip=127.0.0.1",
                "-rpcport=%d" % port,
                "-rpcuser=regtest",
                "-rpcpassword=disposable-local-test",
                "-datadir=" + tmp,
                *extra,
            ]
            process = subprocess.Popen(
                args,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError((Path(tmp) / "console.log").read_text())
                try:
                    rpc("getblockcount")
                    return
                except Exception:
                    time.sleep(0.1)
            raise RuntimeError("Node startup timeout")

        def stop():
            if process and process.poll() is None:
                rpc("stop")
                process.wait(timeout=30)

        try:
            start()
            cases = []
            kinds = (
                "p2pkh",
                "p2sh",
                "p2wpkh",
                "p2sh-p2wpkh",
                "p2wsh",
                "p2sh-p2wsh",
                "p2tr",
                "tapscript",
            )
            for kind in kinds:
                p = make_psbt(kind)
                spk = p.inputs[0].utxo.script_pubkey
                address = spk.address(NETWORKS["regtest"])
                block = rpc("generatetoaddress", 1, address)[0]
                coinbase = rpc("getblock", block, 2)["tx"][0]
                prev = Transaction.parse(bytes.fromhex(coinbase["hex"]))
                vout = next(
                    i for i, out in enumerate(prev.vout) if out.script_pubkey == spk
                )
                inp = p.inputs[0]
                inp.txid, inp.vout = prev.txid(), vout
                if kind in ("p2pkh", "p2sh"):
                    inp.non_witness_utxo = prev
                else:
                    inp.witness_utxo = prev.vout[vout]
                p.outputs[0].value = prev.vout[vout].value - 10000
                cases.append((kind, p))
            sink = script.p2wpkh(PUB).address(NETWORKS["regtest"])
            rpc("generatetoaddress", 100, sink)
            raws = []
            for kind, p in cases:
                assert sign_psbt(p, ROOT) == 1
                if kind == "tapscript":
                    tx = Transaction.parse(p.tx.serialize())
                    sig = next(iter(p.inputs[0].taproot_sigs.values()))
                    control, leaf = next(iter(p.inputs[0].taproot_scripts.items()))
                    tx.vin[0].witness = script.Witness([sig, leaf[:-1], control])
                elif kind == "p2sh":
                    tx = Transaction.parse(p.tx.serialize())
                    sig = p.inputs[0].partial_sigs[PUB]
                    redeem = p.inputs[0].redeem_script.data
                    tx.vin[0].script_sig = script.Script(
                        b"\x00"
                        + bytes([len(sig)])
                        + sig
                        + bytes([len(redeem)])
                        + redeem
                    )
                else:
                    tx = finalize_psbt(p)
                raw = tx.serialize().hex()
                before = rpc("testmempoolaccept", [raw], 0)[0]
                assert not before["allowed"], (kind, before)
                assert "missing" not in before.get("reject-reason", "").lower(), before
                print(
                    kind, "pre-fork rejection:", before.get("reject-reason"), flush=True
                )
                raws.append((kind, raw))
            activation = rpc("getblockcount") + 1
            stop()
            start(
                [
                    "-testactivationheight=blake2b@%d" % activation,
                    "-blake2b_headline=Krux disposable regtest",
                    "-rdtsexpiry=%d" % (int(time.time()) + 365 * 86400),
                ]
            )
            rpc("generatetoaddress", 1, sink)
            assert rpc("getdeploymentinfo")["blake2b"]["active"]
            txids = []
            for kind, raw in raws:
                accepted = rpc("testmempoolaccept", [raw], 0)[0]
                assert accepted["allowed"], (kind, accepted)
                if kind == "p2wpkh":
                    source = next(p for name, p in cases if name == kind)
                    for legacy_type in (1, 0x21):
                        bad = Transaction.parse(bytes.fromhex(raw))
                        tx = source.tx
                        vin = tx.vin[0]
                        sc = script.p2pkh_from_p2wpkh(
                            source.inputs[0].utxo.script_pubkey
                        )
                        # Independent BIP143 ALL preimage, allowing the unknown
                        # 0x20 bit as standard-chain consensus does for ECDSA.
                        preimage = (
                            tx.version.to_bytes(4, "little")
                            + hashes.sha256(tx.hash_prevouts())
                            + hashes.sha256(tx.hash_sequence())
                            + bytes(reversed(vin.txid))
                            + vin.vout.to_bytes(4, "little")
                            + sc.serialize()
                            + source.inputs[0].utxo.value.to_bytes(8, "little")
                            + vin.sequence.to_bytes(4, "little")
                            + hashes.sha256(tx.hash_outputs())
                            + tx.locktime.to_bytes(4, "little")
                            + legacy_type.to_bytes(4, "little")
                        )
                        digest = hashes.double_sha256(preimage)
                        sig = CHILD.key.sign(digest).serialize() + b"\x21"
                        bad.vin[0].witness = script.Witness([sig, PUB.sec()])
                        rejected = rpc("testmempoolaccept", [bad.serialize().hex()], 0)[
                            0
                        ]
                        assert not rejected["allowed"], rejected
                        assert (
                            "signature" in rejected.get("reject-reason", "").lower()
                        ), rejected
                    print(
                        "Legacy digests stamped 0x21 rejected on the same unspent output",
                        flush=True,
                    )
                txids.append(rpc("sendrawtransaction", raw, 0))
                print(kind, "unified accepted", flush=True)
            mined = rpc("generatetoaddress", 1, sink)[0]
            assert set(txids).issubset(rpc("getblock", mined)["tx"])
            print(
                "PASS: eight script forms rejected before activation, accepted and mined after activation.",
                flush=True,
            )
        finally:
            stop()
            log.close()


if __name__ == "__main__":
    main()
