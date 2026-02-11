<#
.SYNOPSIS
    Clones or pulls the my-skills repo into each configured target directory.

.DESCRIPTION
    For each target directory:
      - If .git does not exist, clones the repo into that location.
      - If .git exists, pulls the latest changes.

.PARAMETER Pull
    Explicitly pull all existing clones. Without this flag, existing clones are skipped
    and only new targets are cloned.

.EXAMPLE
    .\Sync-Skills.ps1            # Clone to any target that doesn't exist yet
    .\Sync-Skills.ps1 -Pull      # Pull updates for all existing targets
#>
[CmdletBinding()]
param(
    [switch]$Pull
)

$ErrorActionPreference = 'Stop'

$RepoUrl = 'https://github.com/ianphil/my-skills.git'

# Target directories where skills should be synced
$Targets = @(
    (Join-Path $HOME '.copilot' 'skills')
)

foreach ($target in $Targets) {
    $gitDir = Join-Path $target '.git'

    if (Test-Path $gitDir) {
        if ($Pull) {
            Write-Host "Pulling latest in $target ..." -ForegroundColor Cyan
            git -C $target pull --ff-only
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Pull failed for $target"
            }
        }
        else {
            Write-Host "Already cloned: $target (use -Pull to update)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "Cloning into $target ..." -ForegroundColor Green
        $parentDir = Split-Path $target -Parent
        if (-not (Test-Path $parentDir)) {
            New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
        }
        git clone $RepoUrl $target
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Clone failed for $target"
        }
    }
}

Write-Host "`nDone." -ForegroundColor Green
