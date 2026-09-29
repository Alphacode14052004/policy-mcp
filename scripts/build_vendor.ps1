param([string]$Python = 'py', [string[]]$PythonArgs = @('-3.13'))
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$vendorPath = [IO.Path]::GetFullPath((Join-Path $repoRoot 'vendor'))
$buildRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot '.build'))
if ($vendorPath -ne (Join-Path $repoRoot 'vendor') -or $vendorPath -eq [IO.Path]::GetPathRoot($vendorPath)) { throw 'Unsafe vendor path.' }
if (Test-Path -LiteralPath $vendorPath) {
    if ((Get-Item -LiteralPath $vendorPath).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing a redirected vendor directory.' }
}
& $Python @PythonArgs -c "import sys,struct; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8, 'Requires Windows Python 3.13 x64'; assert sys.platform=='win32'"
if ($LASTEXITCODE -ne 0) { throw 'Incompatible Python. No files were removed.' }
New-Item -ItemType Directory -Force -Path $buildRoot | Out-Null
$environmentPath = Join-Path $buildRoot ('vendor-env-' + [guid]::NewGuid().ToString('N'))
& $Python @PythonArgs -m venv $environmentPath
if ($LASTEXITCODE -ne 0) { throw 'Build requires a full Python 3.13 distribution with venv and ensurepip. Target machine does not need pip.' }
$buildPython = Join-Path $environmentPath 'Scripts/python.exe'
$stagingPath = Join-Path $environmentPath 'packages'
$lockPath = Join-Path $repoRoot 'requirements.lock'
foreach ($line in Get-Content -LiteralPath $lockPath) {
    if ($line.Trim() -and -not $line.StartsWith('#') -and $line -notmatch '^[A-Za-z0-9_.-]+==[0-9][A-Za-z0-9_.+!-]*( --hash=sha256:[a-f0-9]{64})*$') { throw 'Lock file must contain only exact package pins and hashes.' }
}
& $buildPython -m pip install --disable-pip-version-check --only-binary=:all: --no-compile --require-hashes --target $stagingPath -r $lockPath --report (Join-Path $environmentPath 'install-report.json')
if ($LASTEXITCODE -ne 0) { throw 'Pinned wheel build failed; existing vendor preserved. Check compatible cp313 win_amd64 wheels and approved network access.' }
New-Item -ItemType Directory -Force -Path $vendorPath | Out-Null
# Each deletion target resolves to an immediate child of this exact vendor path.
foreach ($entry in Get-ChildItem -LiteralPath $vendorPath -Force) {
    if ($entry.Name -eq 'README.md') { continue }
    $resolvedTarget = [IO.Path]::GetFullPath($entry.FullName)
    if ([IO.Path]::GetDirectoryName($resolvedTarget) -ne $vendorPath -or ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Unsafe vendor child.' }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
}
Get-ChildItem -LiteralPath $stagingPath -Force | Copy-Item -Destination $vendorPath -Recurse -Force
Copy-Item -LiteralPath (Join-Path $environmentPath 'install-report.json') -Destination (Join-Path $vendorPath 'install-report.json')
& $buildPython (Join-Path $PSScriptRoot 'vendor_manifest.py') $vendorPath
if ($LASTEXITCODE -ne 0) { throw 'Manifest generation failed.' }
& (Join-Path $PSScriptRoot 'verify_offline.ps1') -Python $Python -PythonArgs $PythonArgs
Write-Host 'Vendor built and checked. Transfer the repository with vendor; do not transfer a virtual environment.'
