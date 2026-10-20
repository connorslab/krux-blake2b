# Build the firmware yourself

A reproducible build lets you check that the published firmware comes from
the published source. You do not need the private signing key to build or
compare `firmware.bin`.

## What you need

- Linux, or Windows with WSL2.
- Git and Docker with the Buildx plugin.
- The source commit named by the release.

The first run builds a compiler and can take over an hour.

## Run the build

Replace `RELEASE_COMMIT` with the full commit from the release:

```sh
git clone https://github.com/connorslab/krux-blake2b.git
cd krux-blake2b
git checkout --detach RELEASE_COMMIT
git submodule update --init --recursive
bash scripts/reproduce.sh
```

The script builds the Yahboom firmware twice from clean firmware build stages.
It stops with an error if either `firmware.bin` or `kboot.kfpkg` differs.
It reuses the compiler stage, not compiled firmware.

Results are in `build/reproduction/RELEASE_COMMIT/`. Compare `SHA256SUMS`
there with the release's checksums. Matching local builds alone are not enough:
your result must also match the actual file you downloaded.

## What is fixed

The build pins the base image by digest, Debian package snapshot, compiler
source commit, Python build dependencies, and repository submodule commits.
Build timestamps come from the source commit rather than your computer's
clock. Firmware builds use UTC and a fixed Python hash seed.

The signature is a separate file. It is deliberately not part of the
reproducible firmware binary.

## Build status

The new signed-update build procedure is undergoing its first comparison.
Until a successful run and matching release checksums are published, there is
no claim that this candidate has passed the reproducibility check.
