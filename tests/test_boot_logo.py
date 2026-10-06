from unittest.mock import MagicMock

import pytest


@pytest.mark.parametrize("width,height,size", [(135, 240, 80), (240, 320, 112)])
@pytest.mark.parametrize("background,expected", [(0x0000, (0, 0, 0)), (0xFFFF, (255, 255, 255))])
def test_transparent_boot_logo(m5stickv, mocker, width, height, size, background, expected):
    from krux.boot_logo import draw_boot_logo
    from krux import boot_logo_data
    from krux.themes import theme
    import image
    import lcd

    mocker.patch.object(theme, "bg_color", background)
    picture = MagicMock()
    mocker.patch.object(image, "Image", return_value=picture, create=True)
    display = MagicMock()
    display.width.return_value = width
    display.height.return_value = height
    draw_boot_logo(display)
    image.Image.assert_called_once_with(size=(size, size))
    # All pixels are initialized; fully transparent corners match the theme.
    assert picture.set_pixel.call_count == size * size
    assert picture.set_pixel.call_args_list[0].args == (0, 0, expected)
    assert picture.set_pixel.call_args_list[-1].args == (size - 1, size - 1, expected)
    top = max(0, (height - size - 72) // 2)
    lcd.display.assert_called_with(picture, oft=((width - size) // 2, top))
    assert top + size + 8 + 64 <= height
    rgba = getattr(boot_logo_data, "RGBA_%d" % size)
    assert len(rgba) == size * size * 4
    assert any(0 < a < 255 for a in rgba[3::4])  # antialiased alpha edge
