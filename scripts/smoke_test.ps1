param([string]$Python = 'py', [string[]]$PythonArgs = @('-3.13'))
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
& $Python @PythonArgs (Join-Path $PSScriptRoot 'demo.py') --output (Join-Path $repoRoot 'eval/results/smoke.json')
if ($LASTEXITCODE -ne 0) { throw 'Mixed-cart smoke failed.' }
Write-Host 'Fresh temporary demo state passed authorization and changed-cart block.'
