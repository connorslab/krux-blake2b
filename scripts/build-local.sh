#!/usr/bin/env bash
set -euo pipefail
source_repo=${1:?Windows checkout path required}
mode=${2:-build}
export DEBIAN_FRONTEND=noninteractive
if ! command -v docker >/dev/null || ! docker buildx version >/dev/null 2>&1; then
    apt-get update
    apt-get install -y ca-certificates git docker.io docker-buildx python3-venv
fi
service docker start
docker info >/dev/null
if [ "$mode" = setup ]; then
    echo 'Local prerequisites ready. Run build-local.ps1 without -SetupOnly to build.'
    exit 0
fi
# Keep the checkout and Docker layers inside Linux for faster disk access.
work=/opt/krux-local/repo
mkdir -p /opt/krux-local
if [ ! -d "$work/.git" ]; then
    git clone --no-hardlinks "$source_repo" "$work"
fi
cd "$work"
if [ -n "$(git status --porcelain)" ]; then
    echo 'Local build checkout has changes; preserve/review them before rebuilding.' >&2
    exit 1
fi
git fetch "$source_repo" HEAD
git checkout --detach FETCH_HEAD
# Relative submodule URLs resolve against GitHub, not the Windows checkout.
git remote set-url origin https://github.com/connorslab/krux-blake2b.git
git submodule sync --recursive
git submodule update --init --recursive
docker build --build-arg DEVICE=maixpy_yahboom -t krux-yahboom-local .
container=$(docker create krux-yahboom-local)
trap 'docker rm "$container" >/dev/null' EXIT
output="$source_repo/build/local-yahboom"
mkdir -p "$output"
docker cp "$container:/src/firmware/Kboot/build/firmware.bin" "$output/firmware.bin"
docker cp "$container:/src/firmware/Kboot/build/kboot.kfpkg" "$output/kboot.kfpkg"
git rev-parse HEAD > "$output/SOURCE-COMMIT.txt"
(cd "$output" && sha256sum firmware.bin kboot.kfpkg > SHA256SUMS.txt)
echo "Firmware saved to $output"
