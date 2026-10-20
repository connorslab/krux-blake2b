"""Host signing output must be accepted by the exact library used on device."""
import hashlib
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from embit import ec as device_ec


def test_signer_interoperability_and_tamper_rejection(tmp_path):
    key = ec.generate_private_key(ec.SECP256K1())
    private = tmp_path / "private.pem"
    public = tmp_path / "public.pem"
    binary = tmp_path / "firmware.bin"
    signature = tmp_path / "firmware.bin.sig"
    password = b"test-only-password"
    private.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password)))
    public.write_bytes(key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    binary.write_bytes(b"disposable test firmware")
    tool = Path(__file__).resolve().parents[1] / "scripts/firmware-sign.py"
    command = [sys.executable, str(tool), "sign", str(binary),
               "--key", str(private), "--signature", str(signature)]
    subprocess.run(command, input=password + b"\n", check=True, capture_output=True)
    compressed = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)
    verifier = device_ec.PublicKey.parse(compressed)
    assert verifier.verify(device_ec.Signature.parse(signature.read_bytes()),
                           hashlib.sha256(binary.read_bytes()).digest())
    # Signing again cannot overwrite a released signature.
    assert subprocess.run(command, input=password + b"\n", capture_output=True).returncode != 0
    verify = [sys.executable, str(tool), "verify", str(binary),
              "--key", str(public), "--signature", str(signature)]
    subprocess.run(verify, check=True, capture_output=True)
    binary.write_bytes(b"changed")
    assert subprocess.run(verify, capture_output=True).returncode != 0
