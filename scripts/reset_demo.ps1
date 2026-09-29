$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$runtimePath = [IO.Path]::GetFullPath((Join-Path $repoRoot 'runtime'))
if (Test-Path -LiteralPath $runtimePath) {
    if ((Get-Item -LiteralPath $runtimePath).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing redirected runtime.' }
}
# Stop the VS Code server before resetting. Keep the signing key for deliberate
# restart tests; delete only named repository-owned demo database files.
foreach ($name in @('offerproof.sqlite3', 'offerproof.sqlite3-wal', 'offerproof.sqlite3-shm')) {
    $targetPath = [IO.Path]::GetFullPath((Join-Path $runtimePath $name))
    if ([IO.Path]::GetDirectoryName($targetPath) -ne $runtimePath) { throw 'Unsafe reset path.' }
    if (Test-Path -LiteralPath $targetPath) { Remove-Item -LiteralPath $targetPath -Force }
}
Write-Host 'Demo database reset. Signing key preserved. Start the server again.'
