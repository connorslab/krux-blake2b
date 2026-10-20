# Paperclip Krux

An offline Bitcoin Blake2b (XBT) transaction signer, based on [Krux](https://github.com/selfcustody/krux). Prepare transactions in a compatible wallet, review and sign them on the device, then return the signed transaction by QR code or microSD.

## Current release

**[v26.09.0-xbt.2](https://github.com/connorslab/krux-blake2b/releases/tag/v26.09.0-xbt.2)** is published as a prerelease for the **Yahboom K210** (`maixpy_yahboom`), based on Krux v26.09.0.

| Download or guide | Use |
| --- | --- |
| [USB flashing instructions](docs/FIRMWARE-UPDATES.md#first-installation-windows-macos-or-linux) | Install the complete firmware package using Python on Windows, macOS or Linux. |
| [Release files](https://github.com/connorslab/krux-blake2b/releases/tag/v26.09.0-xbt.2) | Firmware, USB package, signatures and checksums. |
| [Installation and updates](docs/FIRMWARE-UPDATES.md) | USB installation and future signed SD updates. |
| [Reproduce the build](docs/REPRODUCIBLE-BUILD.md) | Build and compare the exact released firmware. |
| [Signing keys](keys/README.md) | Public firmware key and authenticated release-key provenance. |

**Already running an older release?** Releases through `v26.09.0-xbt.1`
need one USB installation of this build to enable future signed SD updates.
The on-device version is `26.09.0`; subsequent SD updates must have a newer
on-device version. Changing only the GitHub release suffix is not sufficient.

[Shrike by privkeyio](https://github.com/privkeyio/shrike) is a compatible
companion wallet for preparing transactions and broadcasting after signing.

## Release verification

- [Regression tests](https://github.com/connorslab/krux-blake2b/actions/runs/39449586428): **1,220 passed**, plus the Knots regtest covering eight script forms.
- [Reproducibility check](https://github.com/connorslab/krux-blake2b/actions/runs/39449585269): two clean firmware build stages produced identical firmware and USB packages, using a shared pinned compiler stage.
- The released firmware signature passed verification with the device's signature library.

## Firmware updates: verified by the signer

The installed Paperclip firmware contains the **Paperclip Holdings LLC firmware
public key**. It verifies the vendor signature on a new firmware image itself,
before activating that image. You do not have to trust your computer to make
that decision.

For an SD update, put the newer release's `firmware.bin` and `firmware.bin.sig`
in the root of the microSD card, insert it, and restart the signer. The signer
checks the signature, device model and version, then asks you to approve the
update on its screen. It writes the inactive firmware slot and checks the
written bytes and boot checksum before activating it.

Older firmware with SD updates disabled needs **one USB installation** of the
signed-update firmware. Subsequent updates can use this on-device verification
path. This is signed-update verification, not hardware-enforced secure boot:
USB flashing can replace the firmware and its embedded key.

See [installation and update instructions](docs/FIRMWARE-UPDATES.md).
The [public key and its authenticated provenance](keys/README.md) are in this
repository. The private signing key is not.

## Build the exact firmware binary yourself

You can build `firmware.bin` without the vendor's private signing key. The
signature is a separate file, so it does not change the firmware you reproduce.

On Linux or WSL2, with Git and Docker Buildx installed:

```sh
git clone https://github.com/connorslab/krux-blake2b.git
cd krux-blake2b
git checkout --detach fd75a549d3f0ff3d87e6f57c0ffece8420a748ab
git submodule update --init --recursive
bash scripts/reproduce.sh
```

These commands reproduce `v26.09.0-xbt.2` from its exact release source commit.
The script rebuilds the firmware twice and requires both `firmware.bin` and
`kboot.kfpkg` to match byte for byte. It fixes the build timestamp and uses
pinned build dependencies.

Then compare your result with the actual downloaded firmware:

```sh
cmp build/reproduction/fd75a549d3f0ff3d87e6f57c0ffece8420a748ab/1/firmware.bin /path/to/downloaded/firmware.bin
```

No output and exit status zero means the files are identical. See the
[build guide](docs/REPRODUCIBLE-BUILD.md) for output files and build status.
The [successful build comparison](https://github.com/connorslab/krux-blake2b/actions/runs/39449585269)
produced firmware SHA-256
`bd8f51115083931b05b8291351479799450b9dce9259e2501816b63ce34f36b7`.

## Compatibility changes

Transaction signing requires `SIGHASH_UNIFIED | SIGHASH_ALL`, byte `0x21`.
There is no standard-chain signing switch or automatic downgrade.

- Pins [privkeyio/embit](https://github.com/privkeyio/embit) at `087d020fbfb66fc2e0eab88fb948269e1da28e95`, including unified hashing and PSBT negotiation. Tests and firmware builds use this same submodule pin.
- Requires every input to explicitly request **unified ALL (`0x21`)**. Missing/default, standard ALL, NONE, SINGLE, ANYONECANPAY and unknown modes fail before any signatures are produced.
- Uses Bitcoin as the currency name and XBT for transaction amounts. Shows a Bitcoin/unified confirmation before transaction review. QR exports preserve the explicit sighash declaration.
- Rejects existing standard signatures and finalized inputs. Multisig coordinators must exchange unfinalized PSBTs and use unified ALL for every signer.
- Adds conservative checks for reduced-data (RDTS) rules: output-script size, script push size, taproot control blocks, tapscript conditionals and oversized unsigned transactions. Corrects the Taproot key-path fee estimate for its explicit sighash byte.
- Disables arbitrary/raw-hash message signing, which could bypass the transaction policy. Bitcoin-prefixed address-message proofs remain available; those proofs are not chain-specific.
- Identifies the fork at startup. SD updates are verified on the device using the dedicated Paperclip Holdings firmware key, then checked by reading back flash before activation. Upstream Krux keys are not accepted.

BLAKE2b is the chain's proof-of-work algorithm. The unified signature digest itself uses the specified `UnifiedSighash` tagged SHA-256 hash. Transaction IDs, BIP39/BIP32 derivation and address checksums retain their specified algorithms. Read the [chain differences](docs/BLAKE2B.md).

## Signing workflow

1. Connect a compatible coordinator, such as [Shrike](https://github.com/privkeyio/shrike), to Bitcoin using the required BLAKE2b proof-of-work consensus rules.
2. Export an unfinalized PSBT with explicit unified ALL (`0x21`) on all inputs and all spent-output amounts/scripts.
3. Import by QR or SD. Confirm the chain prompt, then review destinations, amounts, change and fees on the device.
4. Export the signed PSBT. The coordinator finalizes it and the fork-aware node validates and broadcasts it.

An offline signer cannot prove which chain supplied an address or PSBT. Replay protection comes from the unified signature being invalid under standard-chain rules. It does not distinguish two forks implementing the same unified algorithm, nor prevent standard signatures made elsewhere from replaying onto this chain.

## Requirements

- Host development: Python 3.11/3.12. Linux is recommended for the native BC-UR module and firmware toolchain. The small cryptographic policy suite also runs on Windows.
- Hardware target for the reproducible build: Yahboom K210 (`maixpy_yahboom`).
- Consensus reference: Bitcoin Knots `v29.4.2.knots20260508`, commit `58398baf33e588779685ead478e6397bb28ed3d6`.
- Legacy inputs retain Krux's verified previous-transaction requirement. Standard-chain PSBTs require deliberate preparation by a fork-aware coordinator; the signer does not silently convert them.

Encrypted mnemonic storage is inherited from Krux. This is not a new secure-element design or a claim of physical extraction resistance. Keep an independent seed backup.

## Build and test

```sh
git clone --recursive https://github.com/connorslab/krux-blake2b.git
cd krux-blake2b
python -m venv .venv
. .venv/bin/activate
python -m pip install -e vendor/embit ./firmware/MaixPy/components/micropython/port/src/bc-ur pytest pytest-mock pycryptodome pyqrcode cryptography
python -m pytest -q tests fork_tests vendor/embit/tests/tests/test_unified_sighash.py vendor/embit/tests/tests/test_unified_sighash_negotiation.py
PYTHONPATH=src python fork_tests/regtest.py /path/to/bitcoind
```

The node test uses temporary local regtest storage and disposable coins. It does not connect to your wallet or a public network. See [validation and provenance](docs/BLAKE2B-VALIDATION.md).

For the complete simulator/firmware toolchain and assembly details, see the [original README](docs/UPSTREAM_README.md). Its standard-chain release links do not install this fork. Hardware-build and documentation workflows are manual; the BLAKE2b regression workflow runs on pushes.

Not affiliated with or endorsed by Krux, privkeyio or Bitcoin Knots. Original attribution and [licenses](LICENSE.md) are retained.
