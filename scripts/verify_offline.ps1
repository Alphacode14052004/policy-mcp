param([string]$Python = 'py', [string[]]$PythonArgs = @('-3.13'))
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
& $Python @PythonArgs -c "import sys,struct; assert sys.version_info[:2]==(3,13) and struct.calcsize('P')==8"
if ($LASTEXITCODE -ne 0) { throw 'Requires target Python 3.13 x64.' }
$previousNoIndex = $env:PIP_NO_INDEX
$previousNoBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:PIP_NO_INDEX = '1'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & $Python @PythonArgs (Join-Path $PSScriptRoot 'vendor_manifest.py') (Join-Path $repoRoot 'vendor') --verify
    if ($LASTEXITCODE -ne 0) { throw 'Vendor integrity failed.' }
    & $Python @PythonArgs (Join-Path $PSScriptRoot 'offline_check.py')
    if ($LASTEXITCODE -ne 0) { throw 'Offline import/startup/smoke verification failed.' }
    & $Python @PythonArgs (Join-Path $PSScriptRoot 'run_tests.py') --output (Join-Path $repoRoot 'eval/results/tests-offline.json')
    if ($LASTEXITCODE -ne 0) { throw 'Local test suite failed.' }
} finally {
    $env:PIP_NO_INDEX = $previousNoIndex
    $env:PYTHONDONTWRITEBYTECODE = $previousNoBytecode
}
Write-Host 'Offline verification passed; no pip installation or dependency download was used.'
