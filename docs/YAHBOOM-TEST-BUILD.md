# Yahboom K210 Bitcoin (XBT) test firmware

Target: Yahboom K210 Vision Sensor / Vision Recognition Module with the
2-inch touchscreen (`maixpy_yahboom`). This is not a K230 image.

This is experimental firmware. USB installation and serial startup have been
checked on a physical Yahboom K210. Touchscreen navigation, camera QR scanning,
seed persistence and transaction signing still require functional checks. Use
a disposable test seed and unfunded wallet for those checks.

## Verified build output

The [first successful Yahboom build](https://github.com/connorslab/krux-blake2b/actions/runs/35803283044)
compiled source commit `7963857bd5062342f651fa19f38c6c80c7437180`.
The subsequent documentation commits do not change the firmware source.

- `firmware.bin`: 1,615,104 bytes (below the 3 MiB bootloader limit).
- Firmware SHA-256: `0c09a6eec421759db1b4bb560e9ed534e7a9aa73ecc22b925741eb94e15709c8`.
- `kboot.kfpkg`: 822,948 bytes.
- Package SHA-256: `28c6515b6e709ad0ef975ceaf92a05ea274fa07ad5f643106d1d6171c7fd19e5`.

Package CRCs, flash addresses and embedded-file equality were checked after
download. The binary contains the fork branding and signing-policy strings.
These checks establish build/package integrity, not hardware operation.
The [source-commit signing CI](https://github.com/connorslab/krux-blake2b/actions/runs/35803283324)
also passed, including the forked-node transaction checks.

## Build

Run the repository's **Build** GitHub Actions workflow with device
`maixpy_yahboom`. Download the `build-yahboom` artifact. The initial Docker
build compiles the Kendryte toolchain and can take an hour or more.
The workflow run identifies the exact source commit; the embit and MaixPy
dependencies are pinned as Git submodules.

## First installation on Windows

1. Connect the device using a USB data cable. Find its COM port in Device
   Manager under **Ports (COM & LPT)**. Install the manufacturer's USB serial
   driver if it does not appear.
2. Use the complete `kboot.kfpkg` package for initial installation. It includes
   both bootloaders, configuration and firmware; do not flash `firmware.bin`
   alone at address zero.
3. From a checkout with the pinned Kboot submodule and Python installed:

   ```powershell
   python -m pip install pyserial==3.4
   python firmware/Kboot/build/ktool.py -B goE -b 1500000 -p COM6 path/to/kboot.kfpkg
   ```

   Replace `COM6` with the actual port. Yahboom requires an explicit port.
   Do not disconnect power until flashing completes. If communication is
   unreliable, retry with a lower baud rate such as `115200`.
4. Restart and verify the **Krux Bitcoin** startup branding. Use USB power;
   this module does not include a battery.

The fork has no provisioned firmware signing key. SD firmware upgrades are
deliberately disabled; use USB flashing for this test build. Never select an
upstream automatic installer that replaces this image with standard Krux.

## Arrival checks

- Record the PCB revision and test the touchscreen and buttons.
- Scan QR codes from a disposable wallet, including animated transaction QR.
- Create an encrypted test-seed backup on a compatible microSD card, restart,
  and verify recovery with the correct password and refusal with a wrong one.
- Sign a Bitcoin test transaction using explicit unified SIGHASH_ALL `0x21`.
- Verify the signature with a compatible node, and verify that a PSBT with
  missing or legacy sighash values is refused.

See [chain rules](BLAKE2B.md) and [software validation](BLAKE2B-VALIDATION.md)
for the scope and limitations of the existing tests.

## Bitcoin/XBT build installed on 2026-10-06

Source commit: `f181e6864c5d390dcd2f2c37fda57e5708e77444`.
[Build run](https://github.com/connorslab/krux-blake2b/actions/runs/37482234091)
and [signing tests](https://github.com/connorslab/krux-blake2b/actions/runs/37482234682) passed.

- Firmware size: 1,615,104 bytes.
- Firmware SHA-256: `4bf47be4daf0b64ebfb5a64089aaa6fb9e982d49ecb4e45642c0603eaa839e3e`.
- Package SHA-256: `28097345c28b2e4fc8a3de1112b15c193f29bdcabaafd8178f9694505739786d`.
- Package CRCs, flash addresses, embedded files and Bitcoin/XBT branding checked.
- USB flashing through CH340 completed successfully; bootloader reported App ok
  and started the new image without a traceback in the captured startup log.
- Runtime detected a GC2145 camera sensor. QR scanning was not tested.
- SD was absent from the device during startup; the separate PC card was
  formatted FAT32/MBR and received a hash-verified copy of the USB-install bundle.
  That copy does not enable SD firmware upgrades.
