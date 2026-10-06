param([switch]$SetupOnly)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$distro = 'Ubuntu-24.04'
$distros = (& wsl.exe --list --quiet) -replace "`0", ''
if ($distros -notcontains $distro) {
    & wsl.exe --install -d $distro --no-launch --web-download
    if ($LASTEXITCODE -ne 0) { throw 'Ubuntu installation failed. Restart Windows if WSL requested it, then retry.' }
}
& wsl.exe -d $distro -u root -- true
if ($LASTEXITCODE -ne 0) { throw 'WSL cannot start. Restart Windows to activate the installed features, then retry.' }
$linuxRepo = (& wsl.exe -d $distro -u root -- wslpath -a $repo).Trim()
$linuxScript = "$linuxRepo/scripts/build-local.sh"
$mode = if ($SetupOnly) { 'setup' } else { 'build' }
& wsl.exe -d $distro -u root -- bash $linuxScript $linuxRepo $mode
if ($LASTEXITCODE -ne 0) { throw 'Local build/setup failed. Review the output above.' }
