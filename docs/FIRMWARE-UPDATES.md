# Install and update your Paperclip Krux

## Which files do I need?

Choose the release for your device. For the Paperclip Yahboom K210, use
`maixpy_yahboom`.

| What you want to do | Files |
| --- | --- |
| Install for the first time, or replace older firmware with SD updates disabled | `kboot.kfpkg` and the USB flasher |
| Update a device that already trusts the Paperclip firmware key | `firmware.bin` and `firmware.bin.sig` |
| Check who signed a download on your computer | The public key in `keys/` and `scripts/firmware-sign.py` |
| Build the same firmware yourself | The release source commit and `scripts/reproduce.sh` |

## First installation

Existing Paperclip releases through `v26.09.0-xbt.1` have SD updates disabled.
They need a one-time USB installation to add the Paperclip firmware public key.
An SD card cannot enable a feature that the installed firmware does not have.

Use the full `kboot.kfpkg` package for USB installation. Do not flash
`firmware.bin` at address zero. Follow the [USB installation steps](YAHBOOM-TEST-BUILD.md#first-installation-on-windows).
Keep your recovery backup before replacing firmware.

## Updating from an SD card

Once signed-update firmware is installed:

1. Download the newer release for your device.
2. Copy `firmware.bin` and `firmware.bin.sig` to the root of a FAT32 microSD card.
   Keep those filenames exactly as shown.
3. Insert the card and restart the signer.
4. The signer checks the signature, device type and firmware version.
5. Review the version on its screen and approve installation.
6. Restart when installation has finished.

**The installed firmware verifies the signature itself.** The computer only
downloads and copies files. A checksum file or a successful PC verification
does not replace the device's check.

The update is written to the inactive firmware slot. The signer reads it back
and compares it with the signed hash before changing the boot configuration.
Missing, invalid or changed signatures are refused. A release must have a newer
version than the installed firmware.

This authenticates the SD update path; it is not hardware-enforced secure boot.
USB flashing can replace the firmware and its trust key.

## Public signing key

The dedicated identity is **Paperclip Holdings LLC (Krux Firmware Signing)**.
Its public key is in [keys/](../keys/). No private signing key belongs in the
repository or in a firmware image.

The existing Paperclip Holdings release GPG identity signs the key-file
checksums. Its primary fingerprint is:

```text
AC121D21CE3BB408763DD608165128AF9E2F3216
```

GPG establishes the published firmware key's association with Paperclip. The
device uses the embedded secp256k1 key directly; it does not run GPG.

For optional computer-side verification, install Python and `cryptography`,
then run from the repository:

```sh
python scripts/firmware-sign.py verify firmware.bin \
  --key keys/paperclip-firmware-signing-key.pem \
  --signature firmware.bin.sig
```

## Reproduce the firmware

See [Build the firmware yourself](REPRODUCIBLE-BUILD.md).
