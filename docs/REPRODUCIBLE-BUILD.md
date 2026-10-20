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

For release `v26.09.0-xbt.2`, use this exact source commit:

```sh
git clone https://github.com/connorslab/krux-blake2b.git
cd krux-blake2b
git checkout --detach fd75a549d3f0ff3d87e6f57c0ffece8420a748ab
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

Release `v26.09.0-xbt.2` passed the
[two-build comparison](https://github.com/connorslab/krux-blake2b/actions/runs/39449585269).
Both firmware stages were rebuilt without cached firmware output; the compiler
stage was shared. The exact source commit is
`fd75a549d3f0ff3d87e6f57c0ffece8420a748ab`.

| File | SHA-256 |
| --- | --- |
| `firmware.bin` | `bd8f51115083931b05b8291351479799450b9dce9259e2501816b63ce34f36b7` |
| `kboot.kfpkg` | `75d26b082fd25cdfb7cbdcb0b8ace769a68dec2fd5aaa22e34972f8d5b8b9656` |

The separately packaged Windows flasher is not covered by this firmware
reproducibility result. Documentation updates on the main branch do not change
the release's source commit; always check out the commit named above.
