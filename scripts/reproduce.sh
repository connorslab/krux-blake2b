#!/usr/bin/env bash
# Run from a clean, recursive checkout of the published source commit.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -n "$(git status --porcelain --untracked-files=normal)" ]; then
    echo "Use a clean checkout of the release commit." >&2
    exit 1
fi
if git submodule status --recursive | grep -Eq '^[-+U]'; then
    echo "Initialize all submodules at their recorded commits." >&2
    exit 1
fi
commit=$(git rev-parse HEAD)
epoch=$(git show -s --format=%ct HEAD)
output="$(pwd)/build/reproduction/$commit"
mkdir -p "$output"
container=""
trap 'if [ -n "$container" ]; then docker rm "$container" >/dev/null; fi' EXIT
for attempt in 1 2; do
    # Reuse only the compiler stage; rebuild every firmware stage from scratch.
    docker buildx build --load --platform linux/amd64 \
        --no-cache-filter build-software,build-firmware,build \
        --build-arg DEVICE=maixpy_yahboom \
        --build-arg SOURCE_DATE_EPOCH="$epoch" \
        --tag "paperclip-krux-reproduce:$attempt" .
    container=$(docker create "paperclip-krux-reproduce:$attempt")
    mkdir -p "$output/$attempt"
    docker cp "$container:/src/firmware/Kboot/build/firmware.bin" "$output/$attempt/"
    docker cp "$container:/src/firmware/Kboot/build/kboot.kfpkg" "$output/$attempt/"
    docker rm "$container" >/dev/null
    container=""
done
cmp "$output/1/firmware.bin" "$output/2/firmware.bin"
cmp "$output/1/kboot.kfpkg" "$output/2/kboot.kfpkg"
printf '%s\n' "$commit" > "$output/SOURCE-COMMIT.txt"
printf '%s\n' "$epoch" > "$output/SOURCE_DATE_EPOCH.txt"
git submodule status --recursive > "$output/SUBMODULES.txt"
(cd "$output/1" && sha256sum firmware.bin kboot.kfpkg) > "$output/SHA256SUMS"
echo "Both clean firmware builds match. Results: $output"
