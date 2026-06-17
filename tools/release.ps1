<#
.SYNOPSIS
    Release automation for market-intel.

.DESCRIPTION
    Mechanizes the 11-step release process so nothing relies on the operator
    remembering. Implements PHILOSOPHY.md P2 ("机制不靠意图"): every release
    in v0.17-v0.22 forgot at least one gate (sync-check, verify_matrix,
    CHANGELOG header). This script makes them all fail-closed.

.PARAMETER Version
    Semver string without the "v" prefix, e.g. 0.23.0. Positional or named.

.PARAMETER DryRun
    Runs every validation but skips the git mutations (add/commit/tag/push).
    Use to confirm CHANGELOG + plugin.json + matrix + sync-check are green
    before committing to the release.

.EXAMPLE
    .\tools\release.ps1 -Version 0.23.0 -DryRun
    .\tools\release.ps1 0.23.0
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Version,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# --- locate repo root (this script lives at <repo>/tools/release.ps1) ---
$RepoRoot   = Split-Path -Parent $PSScriptRoot
$ConfigRepo = "C:\Users\<username>\CodesSelf\market-intel-config"
$Today      = Get-Date -Format "yyyy-MM-dd"
$Tag        = "v$Version"

Set-Location $RepoRoot

Write-Host "=== market-intel release ==="
Write-Host "repo:    $RepoRoot"
Write-Host "version: $Version"
Write-Host "tag:     $Tag"
Write-Host "today:   $Today"
if ($DryRun) { Write-Host "mode:    DRY RUN (no git mutations)" -ForegroundColor Yellow }
Write-Host ""

function Abort-Release($step, $msg) {
    Write-Host ""
    Write-Host "[ABORT @ step $step] $msg" -ForegroundColor Red
    exit 1
}

# ---------------------------------------------------------------------------
# Step 1: working tree clean
# ---------------------------------------------------------------------------
Write-Host "[1/11] working tree clean check"
$dirty = git status --porcelain
if (-not $?) { Abort-Release 1 "git status failed" }
if ($dirty) {
    Write-Host "       uncommitted changes detected:" -ForegroundColor Red
    $dirty | ForEach-Object { Write-Host "         $_" }
    Abort-Release 1 "working tree not clean; commit or stash first"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 2: CHANGELOG top entry matches "## [<version>] - <today>"
# ---------------------------------------------------------------------------
Write-Host "[2/11] CHANGELOG.md header check"
$changelogPath = Join-Path $RepoRoot "CHANGELOG.md"
if (-not (Test-Path $changelogPath)) { Abort-Release 2 "CHANGELOG.md not found at $changelogPath" }

$lines = Get-Content $changelogPath
# skip "# Changelog" + blanks; collect first ~5 non-empty lines after it
$afterHeader = $false
$candidates = @()
foreach ($line in $lines) {
    if (-not $afterHeader) {
        if ($line -match '^\s*#\s+Changelog\s*$') { $afterHeader = $true }
        continue
    }
    if ($line.Trim() -eq "") { continue }
    $candidates += $line
    if ($candidates.Count -ge 5) { break }
}

# Accept either ASCII "-" or em-dash "—" between version and date — match what's already in the file
$expectedAscii = "## [$Version] - $Today"
$expectedEm    = "## [$Version] $([char]0x2014) $Today"
$pattern = '^\s*##\s*\[' + [regex]::Escape($Version) + '\]\s*[-' + [char]0x2014 + ']\s*' + [regex]::Escape($Today) + '\s*$'

$found = $null
foreach ($cand in $candidates) {
    if ($cand -match $pattern) { $found = $cand; break }
}

if (-not $found) {
    Write-Host "       expected (either form):" -ForegroundColor Red
    Write-Host "         $expectedAscii"
    Write-Host "         $expectedEm"
    Write-Host "       found in first 5 non-empty lines after '# Changelog':" -ForegroundColor Red
    if ($candidates.Count -eq 0) {
        Write-Host "         <none>"
    } else {
        $candidates | ForEach-Object { Write-Host "         $_" }
    }
    Abort-Release 2 "CHANGELOG.md top entry does not match version=$Version date=$Today"
}
Write-Host "       OK ($found)"

# ---------------------------------------------------------------------------
# Step 3: bump .claude-plugin/plugin.json version via regex (preserve formatting)
# ---------------------------------------------------------------------------
Write-Host "[3/11] .claude-plugin/plugin.json version bump"
$pluginPath = Join-Path $RepoRoot ".claude-plugin\plugin.json"
if (-not (Test-Path $pluginPath)) { Abort-Release 3 "plugin.json not found at $pluginPath" }

$pluginRaw = Get-Content -Raw -Path $pluginPath
$verRegex  = '"version"\s*:\s*"[^"]+"'
if ($pluginRaw -notmatch $verRegex) {
    Abort-Release 3 "could not locate a `"version`": `"...`" field in plugin.json"
}
$pluginNew = [regex]::Replace($pluginRaw, $verRegex, "`"version`": `"$Version`"", 1)

if ($DryRun) {
    Write-Host "       DRY RUN: would replace version field with `"version`": `"$Version`""
} else {
    # write back with no BOM, keep file encoding stable
    [System.IO.File]::WriteAllText($pluginPath, $pluginNew, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "       OK (wrote version=$Version)"
}

# ---------------------------------------------------------------------------
# Step 4: verify_matrix.py
# ---------------------------------------------------------------------------
Write-Host "[4/11] python tools/verify_matrix.py"
$matrixOut = & python tools/verify_matrix.py 2>&1
$matrixExit = $LASTEXITCODE
if ($matrixExit -ne 0) {
    Write-Host "       verify_matrix.py exited $matrixExit; last 20 lines:" -ForegroundColor Red
    $matrixOut | Select-Object -Last 20 | ForEach-Object { Write-Host "         $_" }
    Abort-Release 4 "matrix gate failed; release blocked"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 5: companion config sync-check (skip if repo absent)
# ---------------------------------------------------------------------------
Write-Host "[5/11] companion config sync-check"
if (-not (Test-Path $ConfigRepo)) {
    Write-Host "       WARN: $ConfigRepo not present; skipping sync-check" -ForegroundColor Yellow
} else {
    Push-Location $ConfigRepo
    try {
        $syncOut  = & python scripts/sync-check.py 2>&1
        $syncExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    if ($syncExit -ne 0) {
        # Parse "[NNN] X - ..." lines to find any bucket B-G > 0. Bucket A is intentional skips.
        $nonABlockers = @()
        foreach ($line in $syncOut) {
            if ($line -match '^\s*\[\s*(\d+)\s*\]\s+([A-G])\s') {
                $count  = [int]$matches[1]
                $bucket = $matches[2]
                if ($bucket -ne 'A' -and $count -gt 0) {
                    $nonABlockers += "bucket ${bucket}: ${count}"
                }
            }
        }
        if ($nonABlockers.Count -gt 0) {
            Write-Host "       sync-check reports drift in non-A buckets:" -ForegroundColor Red
            $nonABlockers | ForEach-Object { Write-Host "         $_" }
            Write-Host "       full output (last 30 lines):" -ForegroundColor Red
            $syncOut | Select-Object -Last 30 | ForEach-Object { Write-Host "         $_" }
            Abort-Release 5 "companion-config sync-check has B-G drift; reconcile before release"
        } else {
            Write-Host "       sync-check exit=$syncExit but only bucket A drift (intentional skips); OK"
        }
    } else {
        Write-Host "       OK (no drift)"
    }
}

# ---------------------------------------------------------------------------
# Stop here in dry-run mode — everything past this point mutates git.
# ---------------------------------------------------------------------------
if ($DryRun) {
    Write-Host ""
    Write-Host "=== DRY RUN complete: validations passed, no git mutations performed ===" -ForegroundColor Green
    Write-Host "Would have:"
    Write-Host "  6.  git add CHANGELOG.md .claude-plugin/plugin.json"
    Write-Host "  7.  git commit -m `"release: v$Version`""
    Write-Host "  8.  git tag $Tag"
    Write-Host "  9.  git push origin main"
    Write-Host "  10. git push origin $Tag"
    Write-Host "  11. print success summary"
    exit 0
}

# ---------------------------------------------------------------------------
# Step 6: git add
# ---------------------------------------------------------------------------
Write-Host "[6/11] git add CHANGELOG.md .claude-plugin/plugin.json"
git add CHANGELOG.md .claude-plugin/plugin.json
if (-not $?) { Abort-Release 6 "git add failed (recovery: git restore --staged .)" }
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 7: git commit
# ---------------------------------------------------------------------------
Write-Host "[7/11] git commit"
git commit -m "release: v$Version"
if (-not $?) {
    Abort-Release 7 "git commit failed (recovery: git restore --staged . ; check pre-commit hooks)"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 8: git tag
# ---------------------------------------------------------------------------
Write-Host "[8/11] git tag $Tag"
git tag $Tag
if (-not $?) {
    Abort-Release 8 "git tag failed (recovery: git reset --soft HEAD~1 to undo the commit)"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 9: git push origin main
# ---------------------------------------------------------------------------
Write-Host "[9/11] git push origin main"
git push origin main
if (-not $?) {
    Abort-Release 9 "git push main failed (recovery: keep local commit + tag, retry push; or 'git reset --hard HEAD~1; git tag -d $Tag' to fully unwind)"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 10: git push tag
# ---------------------------------------------------------------------------
Write-Host "[10/11] git push origin $Tag"
git push origin $Tag
if (-not $?) {
    Abort-Release 10 "git push tag failed (main is already pushed; recovery: retry 'git push origin $Tag', or 'git tag -d $Tag; git push origin :refs/tags/$Tag' to fully unwind)"
}
Write-Host "       OK"

# ---------------------------------------------------------------------------
# Step 11: summary
# ---------------------------------------------------------------------------
$sha = git rev-parse HEAD
Write-Host ""
Write-Host "=== release v$Version complete ===" -ForegroundColor Green
Write-Host "  version: $Version"
Write-Host "  commit:  $sha"
Write-Host "  tag:     $Tag"
Write-Host "  pushed:  origin/main + $Tag"
exit 0
