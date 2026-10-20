# Paperclip firmware public key

These files are public. They let anyone verify firmware signed by
**Paperclip Holdings LLC (Krux Firmware Signing)**.

- `paperclip-firmware-signing-key.pem`: public key for verification tools.
- `paperclip-firmware-signing-key.hex`: the same key embedded in the firmware.
- `firmware-key.json`: identity, purpose and signature format.
- `SHA256SUMS` and `SHA256SUMS.asc`: key-file checksums authenticated by the
  existing Paperclip Holdings release GPG identity.
- `paperclip-release-signing-key.asc`: that identity's public GPG key.

The GPG primary fingerprint is:

```text
AC121D21CE3BB408763DD608165128AF9E2F3216
```

To check the public-key files, run these commands from this directory:

```sh
gpg --import paperclip-release-signing-key.asc
gpg --fingerprint AC121D21CE3BB408763DD608165128AF9E2F3216
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum --check SHA256SUMS
```

Compare the fingerprint with Paperclip's established release identity. A key
downloaded beside a signature is not, by itself, proof of who owns it.

The private firmware key is not published. The device checks update signatures
using the public key already embedded in its installed firmware.
