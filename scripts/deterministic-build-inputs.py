"""Normalize MaixPy's wall-clock build stamp without changing its git submodule."""
from pathlib import Path

path = Path("firmware/MaixPy/tools/kconfig/update_build_info.py")
text = path.read_text()
old = "time_now = time.localtime(time.time())"
if text.count(old) != 1:
    raise RuntimeError("Build timestamp hook changed; review before building")
text = text.replace(
    old,
    'time_now = time.gmtime(int(__import__("os").environ["SOURCE_DATE_EPOCH"]))',
)
path.write_text(text)
# Submodule .git links point outside the Docker build context. Do not let
# host checkout layout or tags influence version detection in the container.
for path in Path("firmware").rglob(".git"):
    if path.is_file():
        path.unlink()
