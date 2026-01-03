#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Literate Test Runner for PowerShell
    Parses markdown test files and validates assertions.

.DESCRIPTION
    Copy this file to your project's tests/ directory:
        Copy-Item run_tests.ps1 /path/to/project/tests/

    Run from project root:
        pwsh tests/run_tests.ps1
#>

$ErrorActionPreference = "Stop"

# Counters
$script:TotalPassed = 0
$script:TotalFailed = 0

# Determine tests directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ((Split-Path -Leaf $ScriptDir) -eq "tests") {
    $TestsDir = $ScriptDir
} else {
    $TestsDir = Join-Path $ScriptDir "tests"
}

if (-not (Test-Path $TestsDir)) {
    Write-Host "No tests/ directory found"
    exit 1
}

function Parse-Frontmatter {
    param([string]$Content, [string]$Key)

    $match = [regex]::Match($Content, "(?ms)^``````toml\s*\n(.*?)^``````")
    if ($match.Success) {
        $frontmatter = $match.Groups[1].Value
        $keyMatch = [regex]::Match($frontmatter, "(?m)^${Key}\s*=\s*[`"']?([^`"'\n]+)[`"']?")
        if ($keyMatch.Success) {
            return $keyMatch.Groups[1].Value
        }
    }
    return $null
}

function Run-Test {
    param(
        [string]$Code,
        [string]$TestName,
        [string[]]$Assertions
    )

    # Create temp script
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    Set-Content -Path $tempScript -Value $Code

    # Execute and capture output
    $stdout = ""
    $stderr = ""
    $exitCode = 0

    try {
        $output = & pwsh -NoProfile -NonInteractive -File $tempScript 2>&1
        $stdout = ($output | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] }) -join "`n"
        $stderr = ($output | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] }) -join "`n"
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) { $exitCode = 0 }
    } catch {
        $stderr = $_.Exception.Message
        $exitCode = 1
    }

    Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue

    $passed = $true
    $failMessage = ""

    foreach ($assertion in $Assertions) {
        if ([string]::IsNullOrWhiteSpace($assertion)) { continue }

        $parts = $assertion -split ":", 2
        $type = $parts[0].Trim()
        $value = if ($parts.Length -gt 1) { $parts[1].Trim() } else { "" }

        switch ($type) {
            "exit" {
                $expectedExit = [int]$value
                if ($exitCode -ne $expectedExit) {
                    $passed = $false
                    $failMessage = "Expected exit code $expectedExit, got $exitCode"
                }
            }
            "stdout" {
                if ($value -match 'contains\("([^"]+)"\)') {
                    $substring = $matches[1]
                    if ($stdout -notlike "*$substring*") {
                        $passed = $false
                        $failMessage = "stdout should contain '$substring'"
                    }
                } elseif ($value -match 'matches\(/([^/]+)/\)') {
                    $pattern = $matches[1]
                    if ($stdout -notmatch $pattern) {
                        $passed = $false
                        $failMessage = "stdout should match /$pattern/"
                    }
                } else {
                    $expected = $value.Trim('"')
                    if ($stdout.Trim() -ne $expected) {
                        $passed = $false
                        $failMessage = "Expected stdout '$expected', got '$($stdout.Trim())'"
                    }
                }
            }
            "stderr" {
                if ($value -match 'contains\("([^"]+)"\)') {
                    $substring = $matches[1]
                    if ($stderr -notlike "*$substring*") {
                        $passed = $false
                        $failMessage = "stderr should contain '$substring'"
                    }
                } elseif ($value -match '\[([^\]]+)\]') {
                    $errorCode = $matches[1]
                    if ($stderr -notlike "*[$errorCode]*") {
                        $passed = $false
                        $failMessage = "stderr should contain [$errorCode]"
                    }
                }
            }
            "throws" {
                # Check if error was thrown with specific type
                if ($exitCode -eq 0) {
                    $passed = $false
                    $failMessage = "Expected exception but none was thrown"
                } elseif ($value -match '\[([^\]]+)\]') {
                    $errorCode = $matches[1]
                    if ($stderr -notlike "*$errorCode*") {
                        $passed = $false
                        $failMessage = "Expected error [$errorCode], got: $stderr"
                    }
                }
            }
        }
    }

    if ($passed) {
        Write-Host "  $([char]0x2713) $TestName" -ForegroundColor Green
        $script:TotalPassed++
    } else {
        Write-Host "  $([char]0x2717) $TestName" -ForegroundColor Red
        Write-Host "      $failMessage"
        $script:TotalFailed++
    }
}

function Process-File {
    param([string]$FilePath)

    $content = Get-Content -Path $FilePath -Raw
    $lines = Get-Content -Path $FilePath

    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "  $(Split-Path -Leaf $FilePath)"
    Write-Host ("=" * 60)

    $currentSection = ""
    $currentTest = ""
    $inCodeBlock = $false
    $codeLang = ""
    $codeContent = ""
    $assertions = @()
    $lineNum = 0

    foreach ($line in $lines) {
        $lineNum++

        # Track section headers
        if ($line -match "^##\s+(.+)$") {
            $currentSection = $matches[1]
            Write-Host ""
            Write-Host "  $currentSection"
            Write-Host "  $('-' * $currentSection.Length)"
        } elseif ($line -match "^###\s+(.+)$") {
            $currentTest = $matches[1]
        }

        # Start of code block
        if ($line -match "^``````(ps1|powershell|pwsh)$" -and -not $inCodeBlock) {
            $inCodeBlock = $true
            $codeLang = $matches[1]
            $codeContent = ""
            $assertions = @()
            continue
        }

        # End of code block
        if ($line -eq '```' -and $inCodeBlock) {
            $inCodeBlock = $false
            if ($assertions.Count -gt 0) {
                $testName = if ($currentTest) { $currentTest } else { "Test at line $lineNum" }
                Run-Test -Code $codeContent -TestName $testName -Assertions $assertions
            }
            continue
        }

        # Inside code block
        if ($inCodeBlock) {
            if ($line -match "^#\s*(exit|stdout|stderr|throws):\s*(.+)$") {
                $assertions += "$($matches[1]):$($matches[2])"
            } else {
                $codeContent += "$line`n"
            }
        }
    }
}

# Main
$testFiles = Get-ChildItem -Path $TestsDir -Filter "*.md" -File

if ($testFiles.Count -eq 0) {
    Write-Host "No .md test files found in tests/"
    exit 1
}

foreach ($file in $testFiles | Sort-Object Name) {
    Process-File -FilePath $file.FullName
}

Write-Host ""
Write-Host ("=" * 60)
Write-Host "  Summary: $script:TotalPassed passed, $script:TotalFailed failed"
Write-Host ("=" * 60)
Write-Host ""

if ($script:TotalFailed -gt 0) {
    exit 1
}
