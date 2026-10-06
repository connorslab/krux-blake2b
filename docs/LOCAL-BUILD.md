# Local Yahboom builds on Windows

Install WSL and enable Virtual Machine Platform. Restart Windows when requested.
Then, from PowerShell in this repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-local.ps1 -SetupOnly
powershell -ExecutionPolicy Bypass -File scripts/build-local.ps1
```

The script installs Ubuntu 24.04 if missing and Docker Engine/buildx inside
Ubuntu. Docker Desktop is not required. Installation may show a Windows
administrator prompt. It does not reboot Windows or flash a device.

Commit desired source changes before building. The script builds the Windows
checkout's HEAD in `/opt/krux-local/repo` inside WSL, with pinned submodules.
It stops if that Linux checkout has uncommitted changes. Outputs and SHA-256
checksums go to `build/local-yahboom` in the Windows checkout.

The first build compiles the toolchain and remains slow. Docker caches those
layers locally for later builds; do not prune the cache if speed matters.
Changing the Dockerfile/toolchain can invalidate it. Exact local timings are
not measured yet. Local setup cannot be fully verified until the required
Windows restart has occurred.
