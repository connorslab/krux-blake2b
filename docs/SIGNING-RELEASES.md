# Sign a firmware release

This page is for the release maintainer. Users do not need a private key to
build firmware or check a signature.

1. Build the exact release commit with `bash scripts/reproduce.sh`.
2. Confirm both builds match and run the firmware regression suite.
3. Copy the approved `firmware.bin` to the signing machine.
4. Sign it with the dedicated encrypted secp256k1 private key:

   ```sh
   python scripts/firmware-sign.py sign firmware.bin \
     --key /private/path/firmware-signing-private.pem \
     --signature firmware.bin.sig
   ```

   The script asks for the encryption password without displaying it. For
   automation it also accepts the password on standard input, never as a
   command-line argument.
   Do not put the private key or password in Git, CI, or release artifacts.

5. Verify the result with the public key:

   ```sh
   python scripts/firmware-sign.py verify firmware.bin \
     --key keys/paperclip-firmware-signing-key.pem \
     --signature firmware.bin.sig
   ```

6. Publish the firmware, detached signature, initial-install package, checksums,
   source commit, submodule revisions and reproducibility results together.

The signature is low-S DER-encoded ECDSA over `SHA256(firmware.bin)`, compatible
with the device's existing verification library. The published firmware bytes
must remain unchanged after signing.

Keep an encrypted backup of the private key and its password separately.
Losing this key prevents signing updates for devices that trust it.

For key rotation, the old trusted key must sign the firmware that embeds the
replacement public key. Publishing a replacement key on GitHub does not change
the device's trust. If the old key is unavailable, users need USB installation.
