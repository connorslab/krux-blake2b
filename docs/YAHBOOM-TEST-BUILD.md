# Yahboom K210 BLAKE2b test firmware

Target: Yahboom K210 Vision Sensor / Vision Recognition Module with the
2-inch touchscreen (`maixpy_yahboom`). This is not a K230 image.

This is experimental firmware awaiting a physical device test. Successful
compilation and software tests do not establish camera, touchscreen, storage,
or signing operation on the purchased hardware revision. Use a disposable
test seed and unfunded wallet for the first checks.

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
4. Restart and verify the **Krux BLAKE2b** startup branding. Use USB power;
   this module does not include a battery.

The fork has no provisioned firmware signing key. SD firmware upgrades are
deliberately disabled; use USB flashing for this test build. Never select an
upstream automatic installer that replaces this image with standard Krux.

## Arrival checks

- Record the PCB revision and test the touchscreen and buttons.
- Scan QR codes from a disposable wallet, including animated transaction QR.
- Create an encrypted test-seed backup on a compatible microSD card, restart,
  and verify recovery with the correct password and refusal with a wrong one.
- Sign a BLAKE2b test transaction using explicit unified SIGHASH_ALL `0x21`.
- Verify the signature with a compatible node, and verify that a PSBT with
  missing or legacy sighash values is refused.

See [chain rules](BLAKE2B.md) and [software validation](BLAKE2B-VALIDATION.md)
for the scope and limitations of the existing tests.
