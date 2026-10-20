#!/usr/bin/env python3
"""Offline firmware signing; never use a wallet seed as a release key."""
import argparse
import getpass
import hashlib
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils

ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").digest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["sign", "verify"])
    parser.add_argument("firmware", type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--signature", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "sign":
        # Password arrives over stdin, never a command-line argument.
        password = (
            getpass.getpass("Signing-key password: ").encode()
            if sys.stdin.isatty()
            else sys.stdin.buffer.readline().rstrip(b"\r\n")
        )
        if not password:
            raise ValueError("Encrypted signing key password required on stdin")
        key = serialization.load_pem_private_key(args.key.read_bytes(), password)
        if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(
            key.curve, ec.SECP256K1
        ):
            raise ValueError("Expected a dedicated secp256k1 signing key")
        signature = key.sign(
            digest(args.firmware), ec.ECDSA(utils.Prehashed(hashes.SHA256()))
        )
        r, s = utils.decode_dss_signature(signature)
        signature = utils.encode_dss_signature(r, min(s, ORDER - s))
        key.public_key().verify(
            signature, digest(args.firmware),
            ec.ECDSA(utils.Prehashed(hashes.SHA256())),
        )
        # Never silently replace an existing release signature.
        with args.signature.open("xb") as output:
            output.write(signature)
    else:
        key = serialization.load_pem_public_key(args.key.read_bytes())
        if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(
            key.curve, ec.SECP256K1
        ):
            raise ValueError("Expected a secp256k1 public key")
        key.verify(
            args.signature.read_bytes(), digest(args.firmware),
            ec.ECDSA(utils.Prehashed(hashes.SHA256())),
        )
    print("Firmware signature verified.")


if __name__ == "__main__":
    main()
