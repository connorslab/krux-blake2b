# Krux BLAKE2b

An unofficial fork of [Krux](https://github.com/selfcustody/krux) for the Bitcoin BLAKE2b chain implemented by Bitcoin Knots. **Transaction signing requires the new unified signature hash: `SIGHASH_UNIFIED | SIGHASH_ALL`, byte `0x21`.** There is no standard-chain signing switch or automatic downgrade.

**Experimental source implementation.** Signing has been tested against a disposable Knots regtest node. Physical Krux hardware, production use and R36S/R36XS compatibility have not been verified. No hardware-ready release is claimed.

## Compatibility changes

- Pins [privkeyio/embit](https://github.com/privkeyio/embit) at `087d020fbfb66fc2e0eab88fb948269e1da28e95`, including unified hashing and PSBT negotiation. Tests and firmware builds use this same submodule pin.
- Requires every input to explicitly request **unified ALL (`0x21`)**. Missing/default, standard ALL, NONE, SINGLE, ANYONECANPAY and unknown modes fail before any signatures are produced.
- Shows a BLAKE2b/unified confirmation before transaction review. QR exports preserve the explicit sighash declaration.
- Rejects existing standard signatures and finalized inputs. Multisig coordinators must exchange unfinalized PSBTs and use unified ALL for every signer.
- Adds conservative checks for reduced-data (RDTS) rules: output-script size, script push size, taproot control blocks, tapscript conditionals and oversized unsigned transactions. Corrects the Taproot key-path fee estimate for its explicit sighash byte.
- Disables arbitrary/raw-hash message signing, which could bypass the transaction policy. Bitcoin-prefixed address-message proofs remain available; those proofs are not chain-specific.
- Identifies the fork at startup. **SD firmware updates are disabled** until a fork release-signing key is provisioned. Upstream's key is not trusted to replace this fork. Development builds require manual flashing.

BLAKE2b is the chain's proof-of-work algorithm. The unified signature digest itself uses the specified `UnifiedSighash` tagged SHA-256 hash. Transaction IDs, BIP39/BIP32 derivation and address checksums retain their specified algorithms. Read the [chain differences](docs/BLAKE2B.md).

## Signing workflow

1. Connect a compatible coordinator, such as [Shrike](https://github.com/privkeyio/shrike), to the BLAKE2b chain.
2. Export an unfinalized PSBT with explicit unified ALL (`0x21`) on all inputs and all spent-output amounts/scripts.
3. Import by QR or SD. Confirm the chain prompt, then review destinations, amounts, change and fees on the device.
4. Export the signed PSBT. The coordinator finalizes it and the fork-aware node validates and broadcasts it.

An offline signer cannot prove which chain supplied an address or PSBT. Replay protection comes from the unified signature being invalid under standard-chain rules. It does not distinguish two forks implementing the same unified algorithm, nor prevent standard signatures made elsewhere from replaying onto this chain.

## Requirements

- Host development: Python 3.11/3.12. Linux is recommended for the native BC-UR module and firmware toolchain. The small cryptographic policy suite also runs on Windows.
- Hardware targets: upstream Krux's K210 devices with camera, screen and controls. This fork has not been tested on them. **R36S/R36XS support is deferred.**
- Consensus reference: Bitcoin Knots `v29.4.2.knots20260508`, commit `58398baf33e588779685ead478e6397bb28ed3d6`.
- Legacy inputs retain Krux's verified previous-transaction requirement. Standard-chain PSBTs require deliberate preparation by a fork-aware coordinator; the signer does not silently convert them.

Encrypted mnemonic storage is inherited from Krux. This is not a new secure-element design or a claim of physical extraction resistance. Keep an independent seed backup.

## Build and test

```sh
git clone --recursive https://github.com/connorslab/krux-blake2b.git
cd krux-blake2b
python -m venv .venv
. .venv/bin/activate
python -m pip install -e vendor/embit ./firmware/MaixPy/components/micropython/port/src/bc-ur pytest pytest-mock pycryptodome pyqrcode
python -m pytest -q tests fork_tests vendor/embit/tests/tests/test_unified_sighash.py vendor/embit/tests/tests/test_unified_sighash_negotiation.py
PYTHONPATH=src python fork_tests/regtest.py /path/to/bitcoind
```

The node test uses temporary local regtest storage and disposable coins. It does not connect to your wallet or a public network. See [validation and provenance](docs/BLAKE2B-VALIDATION.md).

For the complete simulator/firmware toolchain and assembly details, see the [original README](docs/UPSTREAM_README.md). Its standard-chain release links do not install this fork. Hardware-build and documentation workflows are manual; the BLAKE2b regression workflow runs on pushes.

Not affiliated with or endorsed by Krux, privkeyio or Bitcoin Knots. Original attribution and [licenses](LICENSE.md) are retained.
