# Validation and provenance

- Krux baseline: `1e7216b11d257fcbe8359325c6046efd74171dd1`.
- Unified embit: `087d020fbfb66fc2e0eab88fb948269e1da28e95`, from privkeyio's `upstream-pr/unified-sighash` branch. The immutable submodule commit controls builds.
- Node reference: `58398baf33e588779685ead478e6397bb28ed3d6`, Knots `v29.4.2.knots20260508`.

## Checks performed

The library's 166 cross-implementation digest vectors cover all four unified script domains; negotiation/error suites also run. `fork_tests/test_blake2b.py` tests real signatures, all disallowed byte values, missing/out-of-range requests, rejection before signing, amount commitments, existing signature modes, duplicate inputs and script boundaries.

The vector file is byte-identical to the pinned node's `src/test/data/unified_sighash.json`, SHA256 `d0d97cad3ac30dfca57d68c638decd643c5abbdede962b5ac3e9fbe90437de2b`. This documents the source of the expected digests rather than deriving expected values with the library being tested.

`tests/test_blake2b_ui.py` exercises the real PSBTSigner, unified signature verification, chain consent/cancellation, fee-warning refusal, and QR/SD export. Hardware/UI services are mocked using upstream's test framework. Obsolete standard-chain signature golden tests now check refusal; new tests cover the changed successful path.

`fork_tests/regtest.py` starts an isolated real node, creates disposable funding outputs, signs through the same helper used by PSBTSigner, and requires refusal before activation. After restart with activation it requires acceptance and mines every spend. P2PKH, P2SH multisig, P2WPKH, nested P2WPKH, P2WSH, nested P2WSH, Taproot key path and simple tapscript **all passed locally**.

RDTS is explicitly enabled on the activated regtest node. Two negative controls sign the old BIP143 message (with type 1 and with type 0x21) but append 0x21; both fail signature verification on the same known-unspent output whose correct unified spend succeeds. CI repeats the real-node test with a checksum-pinned Linux binary.

The application regression suite passed **1,133 tests** at commit `31182f1a`. The final policy/library suite contains **351 tests**, including the 166-vector loop. Test counts are not a count of hardware or consensus scenarios.

The Windows node archive matched the release SHA256SUMS entry:
`8fa3445a0f3ecc7d1f9e4f4778e44c786883437ac781902a38135be5ea0a892b`.
This records checksum comparison, not independent verification of the PGP signer identity.

## Limits

No physical-device testing, R36S port, production signing, seed-storage audit or hardware extraction assessment has been performed. Regtest does not establish the user's live node configuration. Offline checks do not replace full script/consensus validation. There is no replay-isolation claim against another chain implementing the same unified algorithm.

A fork firmware-signing key has not been provisioned; SD firmware updates are disabled instead of accepting standard Krux firmware. For host regression results, inspect the **BLAKE2b signing** Actions run for the exact commit being used. Run commands are in the README.
