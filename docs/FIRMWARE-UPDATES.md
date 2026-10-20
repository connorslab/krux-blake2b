# Install and update your Paperclip Krux

## Which files do I need?

Download [v26.09.0-xbt.2](https://github.com/connorslab/krux-blake2b/releases/tag/v26.09.0-xbt.2).

Choose the release for your device. For the Paperclip Yahboom K210, use
`maixpy_yahboom`.

| What you want to do | Files |
| --- | --- |
| Install for the first time, or replace older firmware with SD updates disabled | `kboot.kfpkg` and the pinned Python `ktool.py` described below |
| Update a device that already trusts the Paperclip firmware key | `firmware.bin` and `firmware.bin.sig` |
| Check who signed a download on your computer | The public key in `keys/` and `scripts/firmware-sign.py` |
| Build the same firmware yourself | The release source commit and `scripts/reproduce.sh` |

## First installation (Windows, macOS or Linux)

Existing Paperclip releases through `v26.09.0-xbt.1` have SD updates disabled.
They need a one-time USB installation to add the Paperclip firmware public key.
An SD card cannot enable a feature that the installed firmware does not have.

Use the full `kboot.kfpkg` package for USB installation. It contains both
bootloaders, configuration and firmware. Do not flash `firmware.bin` at address
zero. Keep your recovery backup before replacing firmware.

1. Install Git and Python 3.11 or 3.12. The commands below use `python`;
   use `python3` on macOS/Linux or `py -3` on Windows if that is your Python
   command.
2. Download `kboot.kfpkg` from the release linked above. Get the flashing tool
   pinned to this release:

   ```sh
   git clone https://github.com/connorslab/krux-blake2b.git
   cd krux-blake2b
   git checkout --detach fd75a549d3f0ff3d87e6f57c0ffece8420a748ab
   git submodule update --init firmware/Kboot
   python -m venv .venv
   ```

3. Activate the environment using the command for your terminal:

   | Terminal | Command |
   | --- | --- |
   | Windows Command Prompt | `.venv\Scripts\activate.bat` |
   | Windows PowerShell | `.venv\Scripts\Activate.ps1` |
   | macOS/Linux bash or zsh | `source .venv/bin/activate` |

   If PowerShell blocks activation, use Command Prompt, or run
   `.venv\Scripts\python.exe` in place of `python` below.

   ```sh
   python -m pip install pyserial==3.4
   python -m serial.tools.list_ports -v
   ```

4. Connect the Yahboom K210 with a USB **data** cable and run the port-list
   command again to identify it. Typical names are `COM6` on Windows,
   `/dev/cu.usbserial-…` on macOS, and `/dev/ttyUSB0` on Linux.
   If no port appears, check the cable and install the manufacturer's USB
   serial driver. On Linux, your account also needs permission to access
   the serial device (commonly through the `dialout` or `uucp` group).
5. Close other serial applications. From the repository folder, run:

   ```sh
   python firmware/Kboot/build/ktool.py -B goE -b 1500000 -p PORT "/path/to/kboot.kfpkg"
   ```

   Replace `PORT` and the quoted package path with your actual values.
   `-B goE` is the setting used for this Yahboom K210 target. Keep USB power
   connected until flashing completes. If communication is unreliable,
   retry with `-b 115200`.
6. Restart the signer and check the Paperclip/Bitcoin startup screen. This
   module uses USB power and does not include a battery.

These steps install the released package; compiling firmware is not required.

## Updating from an SD card

Once signed-update firmware is installed:

1. Download the newer release for your device.
2. Copy `firmware.bin` and `firmware.bin.sig` to the root of a FAT32 microSD card.
   Keep those filenames exactly as shown.
3. Insert the card and restart the signer.
4. The signer checks the signature, device type and firmware version.
5. Review the version on its screen and approve installation.
6. Restart when installation has finished.

This release establishes that update path. It cannot update an older USB-only
release through SD, and reinstalling the same version through SD is refused.
The device's version remains `26.09.0`; a subsequent SD update must carry a
newer on-device version, not just a different GitHub release suffix.

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
