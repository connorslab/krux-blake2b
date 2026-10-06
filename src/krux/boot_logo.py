"""Render the XBT coin with alpha composited over the selected theme."""


def draw_boot_logo(display):
    import image
    import lcd
    from . import boot_logo_data
    from .themes import theme
    from .metadata import FORK_NAME

    size = 80 if display.width() < 200 else 112
    rgba = getattr(boot_logo_data, "RGBA_%d" % size)
    # Krux's LCD theme colors are byte-swapped RGB565.
    color = theme.bg_color
    rgb565 = ((color & 255) << 8) | (color >> 8)
    bg = ((rgb565 >> 11) * 255 // 31,
          ((rgb565 >> 5) & 63) * 255 // 63,
          (rgb565 & 31) * 255 // 31)
    logo = image.Image(size=(size, size))
    for y in range(size):
        for x in range(size):
            i = (y * size + x) * 4
            alpha = rgba[i + 3]
            rgb = tuple((rgba[i + c] * alpha + bg[c] * (255 - alpha) + 127) // 255
                        for c in range(3))
            logo.set_pixel(x, y, rgb)
    top = max(0, (display.height() - size - 72) // 2)
    lcd.display(logo, oft=((display.width() - size) // 2, top))
    display.draw_hcentered_text(FORK_NAME + "\nXBT\nUnified signing only",
                               offset_y=top + size + 8)
