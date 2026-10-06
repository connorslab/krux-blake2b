# XBT boot artwork

Original source: https://neoxa.exchange/logos/btcb2.png (retrieved 2026-10-06).
NeoxEx maps its displayed XBT ticker to this asset. `neoxex-xbt.png` is the
unaltered source; retain its original artwork rights and attribution.

`xbt-smooth.png` is an imagegen-assisted derivative requested by the user to
smooth the transparent outline. It is not a claim of an official NeoxEx logo
revision or endorsement. Prompt: preserve the gold coin artwork, upright
Bitcoin glyph, palette, relief and proportions; repair the outer circular
cutout with smooth antialiased alpha, no fringe, no outside shadow or redesign.

`scripts/compile_boot_logo.py` converts this asset to 80- and 112-pixel frozen
RGBA data using Pillow. The runtime composites alpha over the selected theme
before converting through MaixPy to the display format. No SD image is needed.
