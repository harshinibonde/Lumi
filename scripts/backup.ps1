# Backup SQLite DB and Chroma directory into backups/<timestamp>/.
# Run from repo root:  .\scripts\backup.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$destRoot = Join-Path $repoRoot "backups"
$dest = Join-Path $destRoot $ts
New-Item -ItemType Directory -Path $dest -Force | Out-Null

$db = Join-Path $repoRoot "cognitive_system.db"
$chroma = Join-Path $repoRoot "chroma_storage"

if (Test-Path $db) {
    Copy-Item $db $dest -Force
    Write-Host "Copied cognitive_system.db"
} else {
    Write-Host "Skip: cognitive_system.db not found"
}

if (Test-Path $chroma) {
    Copy-Item $chroma (Join-Path $dest "chroma_storage") -Recurse -Force
    Write-Host "Copied chroma_storage/"
} else {
    Write-Host "Skip: chroma_storage/ not found"
}

Write-Host "Backup folder: $dest"
