"""Exercise verification and activation against simulated flash, with real ECDSA."""
import hashlib
from pathlib import Path

import pytest
from embit import ec
from .shared_mocks import get_mock_open


def test_embedded_key_matches_published_key():
    from krux.metadata import SIGNER_PUBKEY

    public = Path(__file__).resolve().parents[1] / "keys/paperclip-firmware-signing-key.hex"
    assert SIGNER_PUBKEY == public.read_text().strip()
    assert len(ec.PublicKey.from_string(SIGNER_PUBKEY).sec()) == 33


@pytest.mark.parametrize("failure", [
    None, "wrong-key", "changed-sd-file", "trailing-signature",
    "corrupt-flash", "short-read", "bad-header", "bad-boot-checksum",
])
def test_signed_upgrade_activation(mocker, m5stickv, failure):
    from krux import firmware as fw

    key = ec.PrivateKey(b"\x01" * 32)  # Test-only key, never a release key.
    payload = b"test firmware payload" * 1000
    signature = key.sign(hashlib.sha256(payload).digest()).serialize()
    if failure == "wrong-key":
        signature = ec.PrivateKey(b"\x02" * 32).sign(
            hashlib.sha256(payload).digest()).serialize()
    if failure == "trailing-signature":
        signature += b"\x00"
    original_hash = hashlib.sha256(payload).digest()
    if failure == "changed-sd-file":
        payload = b"!" + payload[1:]
    mocker.patch("builtins.open", new=get_mock_open({
        "/sd/firmware.bin": payload, "/sd/firmware.bin.sig": signature,
    }))
    mocker.patch("os.stat", return_value=True)
    mocker.patch("os.remove")
    mocker.patch.object(fw, "SIGNER_PUBKEY", key.get_public_key().to_string())
    from krux.input import BUTTON_ENTER
    input_cls = mocker.patch.object(fw, "Input")
    input_cls.return_value.wait_for_button.return_value = BUTTON_ENTER
    mocker.patch.object(fw, "display")
    mocker.patch.object(fw, "is_this_device", return_value=True)
    mocker.patch.object(fw, "is_version_greater", return_value="99.01.0")
    mocker.patch.object(fw.time, "sleep_ms", create=True)
    memory = bytearray(fw.FLASH_SIZE)
    sector = fw.update_boot_config_sector(bytes(4096), 0, fw.FIRMWARE_SLOT_1, 100)
    memory[fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS:fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS+4096] = sector

    def read(address, count):
        result = bytes(memory[address:address + count])
        if address >= fw.FIRMWARE_SLOT_2:
            if failure == "short-read":
                return result[:-1]
            if failure == "bad-header" and count == 5:
                return b"\xff" * 5
            if failure == "bad-boot-checksum" and address == fw.FIRMWARE_SLOT_2 + 5 + len(payload):
                return b"\xff" * 32
            if failure == "corrupt-flash" and count != 5:
                return b"!" + result[1:]
        return result

    def write(address, data):
        memory[address:address + len(data)] = data

    mocker.patch.object(fw.flash, "read", side_effect=read)
    mocker.patch.object(fw.flash, "write", side_effect=write)
    mocker.patch.object(fw.flash, "erase", side_effect=lambda a, n: write(a, b"\xff" * n))
    activate = mocker.spy(fw, "update_boot_config_sector")
    assert bool(fw.upgrade()) == (failure is None)
    if failure:
        activate.assert_not_called()
        assert bytes(memory[fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS:fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS+4096]) == sector
        if failure in ("wrong-key", "changed-sd-file", "trailing-signature"):
            fw.flash.erase.assert_not_called()
    else:
        activate.assert_called_once()
        assert fw.find_active_firmware(
            memory[fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS:fw.MAIN_BOOT_CONFIG_SECTOR_ADDRESS+4096]
        )[0] == fw.FIRMWARE_SLOT_2
        assert fw.verify_written_firmware(fw.FIRMWARE_SLOT_2, len(payload), original_hash)
