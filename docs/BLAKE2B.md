# Chain differences and offline signing policy

Pinned reference: [Bitcoin Knots v29.4.2.knots20260508](https://github.com/bitcoinknots/bitcoin/tree/58398baf33e588779685ead478e6397bb28ed3d6). Future releases may change these rules.

## Unified signature hash

The [specification](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/doc/unified-sighash.md) and [interpreter](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/src/script/interpreter.cpp) define opt-in bit `0x20`. This wallet permits only `0x21` (unified ALL), although consensus supports other modes.

The preimage includes epoch zero, hash-type byte, transaction version, **five-byte zero-extended locktime**, single-SHA256 aggregates of all prevouts, amounts, spent scripts, sequences and outputs, a script-type domain byte, input index, and the relevant scriptCode/taproot tail. Final digest: `TaggedHash("UnifiedSighash", message)`. The pinned embit supports bare/P2SH, witness v0, taproot key path and tapscript domains.

The type byte alone is insufficient: stamping `0x21` on a legacy digest is not unified signing. Tests verify real digests and node acceptance. Taproot signatures are 65 bytes with the explicit type, rather than 64-byte DEFAULT signatures. All input amounts are committed, addressing the multi-session BIP143 fee-deception attack. Upstream's conservative unverified-amount warning remains.

Protection is one-way against rules without this algorithm. The digest has no unique genesis/network/chain identifier. Shared address prefixes and derivation paths are not chain authentication. Another fork implementing the same algorithm could accept the signature. Standard signatures made elsewhere remain replayable onto this fork wherever the inputs are shared.

## Block weight, headers and deployment

[Consensus constants](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/src/consensus/consensus.h) retain the general 4,000,000-WU block limit and 4,000,000-byte serialization buffer bound. During RDTS the limit is **800,000 weight units**, not 800,000 virtual bytes. Witness scale remains four.

Krux reads transactions/PSBTs, not blocks. It needs neither a larger block parser nor BLAKE2b proof-of-work verification. It rejects an unsigned transaction already at the reduced block weight. This is only a necessary lower-bound check: final witness weight, block/header/coinbase overhead, sigop limits and standardness remain node checks. Fee estimates are not consensus weight validation.

The fork's extended v2 block header and BLAKE2b proof of work affect node/header validation. Normal txid hashing and transaction serialization are unchanged.

[Activation parameters](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/src/kernel/chainparams.cpp): mainnet 961640; testnet4 150308; regtest needs an explicit override. The signer always requires unified ALL and never switches to legacy signing before activation. Test address prefixes also occur on networks without this deployment.

## Reduced-data rules

The reference limits ordinary output scriptPubKeys to 34 bytes and OP_RETURN scriptPubKeys to 83 bytes **including opcodes/push encodings**. It reduces script stack elements to 256 bytes, with the reference's redeem/witness script exceptions; forbids taproot annexes; limits taproot control blocks to seven Merkle nodes (257 bytes); and forbids OP_IF/OP_NOTIF in tapscript.

This fork checks output sizes, provided script pushes, control length/leaf version and tapscript conditionals. It also rejects OP_CODESEPARATOR because the PSBT signer does not track executed separator positions. Checks parse opcodes rather than matching bytes inside pushed data. The signer never constructs an annex and rejects finalized inputs instead of accepting an opaque imported witness. These are conservative checks, not a full script interpreter.

RDTS expires using the **parent block's median time past**, not the device clock: mainnet September 1, 2027 00:00 UTC; testnet4 October 13, 2026 15:00 UTC. This offline policy retains those restrictions after expiry; later expansion requires a deliberate software update.

## Coinbase maturity and node-only checks

The reference retains ordinary 100-block coinbase maturity and adds a temporary long-maturity schedule. On mainnet, start/enforcement is 973440, release 979920, and long maturity 6480 blocks. It applies to the specified coinbase cohort during enforcement, not every historical coinbase. Testnet4 has separate start/enforcement/release heights: 151406/151550/158111. See [parameters](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/src/consensus/params.h) and [input validation](https://github.com/bitcoinknots/bitcoin/blob/58398baf33e588779685ead478e6397bb28ed3d6/src/consensus/tx_verify.cpp).

Krux cannot establish confirmation height, maturity, spentness, chain work or deployment status from a PSBT. The coordinator/node must validate them. MoneyRange remains 21 million coins, with the same satoshi unit, BIP39/BIP32 derivation and address formats.

## Deliberate compatibility limits

Every input must declare unified ALL, including inputs belonging to others. Existing signatures must use the same mode. Finalized inputs, unsupported spent-output types, raw-hash signing and incompatible RDTS scripts are refused. Legacy inputs carrying a witness-UTXO hint are refused to avoid embit selecting the wrong script domain. This can reject some consensus-valid transactions; it never silently falls back to standard signing. Bitcoin-prefixed address-message proofs remain supported but are not chain-specific. Encrypted mnemonic persistence remains upstream behavior.
