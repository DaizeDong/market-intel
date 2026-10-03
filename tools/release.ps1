<#
.SYNOPSIS
    Validate and publish a prepared market-intel release commit on main.
.DESCRIPTION
    Prepare and commit the version, changelog and derived docs first. Both modes
    run all preflight gates. DryRun performs no source, index, tag or push writes.
    Publication requires a verified main commit and verifies both remote refs.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidatePattern('^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$')]
    [string]$Version,
    [Parameter(Mandatory = $true)]
    [string]$ConfigRepo,
    [switch]$DryRun
)
$ErrorActionPreference = "Stop"
$env:GIT_OPTIONAL_LOCKS = '0'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Tag = "v$Version"
$Today = Get-Date -Format 'yyyy-MM-dd'
Set-Location -LiteralPath $RepoRoot

function Read-Git([string[]]$GitArguments) {
    $result = & git -c core.fsmonitor=false @GitArguments
    if ($LASTEXITCODE -ne 0) { throw "Git verification failed: $($GitArguments[0])" }
    return ($result -join "`n").Trim()
}
function Assert-Contract($Payload) {
    $wire = $Payload | ConvertTo-Json -Depth 20 -Compress
    $result = $wire | & python -X utf8 -B (Join-Path $PSScriptRoot 'release_contract.py')
    if ($LASTEXITCODE -ne 0) { throw 'Release checker evidence was rejected' }
    Write-Host ($result -join "`n")
}

try {
    $Branch = Read-Git -GitArguments @('symbolic-ref', '--quiet', '--short', 'HEAD')
    if ($Branch -ne 'main') { throw 'Release requires the main branch' }
    $ReleaseCommit = Read-Git -GitArguments @('rev-parse', '--verify', 'HEAD^{commit}')
    $MainCommit = Read-Git -GitArguments @('rev-parse', '--verify', 'refs/heads/main^{commit}')
    if ($ReleaseCommit -ne $MainCommit) { throw 'HEAD does not match main' }
    if (Read-Git -GitArguments @('status', '--porcelain')) { throw 'Prepare and commit release files before release' }
    $Origin = Read-Git -GitArguments @('remote', 'get-url', '--all', 'origin')
    $PushOrigin = Read-Git -GitArguments @('remote', 'get-url', '--push', '--all', 'origin')
    if (-not $Origin -or $Origin.Contains("`n") -or $Origin -ne $PushOrigin) {
        throw 'Release requires one matching origin fetch and push destination'
    }
    $RemoteMain = Read-Git -GitArguments @('ls-remote', '--exit-code', '--refs', 'origin', 'refs/heads/main')
    $RemoteMainParts = $RemoteMain -split '\s+'
    if ($RemoteMainParts.Count -ne 2 -or $RemoteMainParts[1] -ne 'refs/heads/main') {
        throw 'Remote main could not be verified'
    }
    & git merge-base --is-ancestor $RemoteMainParts[0] $ReleaseCommit
    if ($LASTEXITCODE -ne 0) { throw 'Fetch origin first; remote main must be a known ancestor of this release' }
    if (Read-Git -GitArguments @('tag', '--list', $Tag)) { throw 'Release tag already exists locally' }
    if (Read-Git -GitArguments @('ls-remote', '--refs', 'origin', "refs/tags/$Tag")) { throw 'Release tag already exists remotely' }

    $Plugin = Get-Content -Raw -LiteralPath (Join-Path $RepoRoot '.claude-plugin/plugin.json') | ConvertFrom-Json
    if ($Plugin.version -ne $Version) { throw 'Commit the requested plugin version before release' }
    $Header = Get-Content -LiteralPath (Join-Path $RepoRoot 'CHANGELOG.md') |
        Where-Object { $_ -match '^##\s*\[' } | Select-Object -First 1
    $HeaderPattern = '^##\s*\[' + [regex]::Escape($Version) + '\]\s*[-' + [char]0x2014 + ']\s*' + $Today + '\s*$'
    if ($Header -notmatch $HeaderPattern) { throw 'Top changelog entry must match the release version and today' }

    & python -X utf8 -B (Join-Path $PSScriptRoot 'verify_matrix.py') --base $RemoteMainParts[0]
    if ($LASTEXITCODE -ne 0) { throw 'Matrix gate failed or was not examined' }
    $ConfigRepo = (Resolve-Path -LiteralPath $ConfigRepo).Path
    $SyncScript = Join-Path $ConfigRepo 'scripts/sync-check.py'
    if (-not (Test-Path -LiteralPath $SyncScript -PathType Leaf)) { throw 'Companion sync checker is required' }
    Push-Location -LiteralPath $ConfigRepo
    try {
        $SyncOutput = & python -X utf8 -B $SyncScript 2>&1
        $SyncExit = $LASTEXITCODE
    } finally { Pop-Location }
    Assert-Contract @{kind='sync'; returncode=$SyncExit; output=($SyncOutput -join "`n")}
    $DocOutput = & python -X utf8 -B (Join-Path $PSScriptRoot 'check_doc_drift.py') --json --no-cache 2>&1
    $DocExit = $LASTEXITCODE
    Assert-Contract @{kind='doc'; returncode=$DocExit; output=($DocOutput -join "`n"); version=$Version}
    if ((Read-Git -GitArguments @('rev-parse', '--verify', 'HEAD^{commit}')) -ne $ReleaseCommit -or
        (Read-Git -GitArguments @('symbolic-ref', '--quiet', '--short', 'HEAD')) -ne 'main' -or
        (Read-Git -GitArguments @('status', '--porcelain'))) { throw 'Release state changed during preflight' }
    if ($DryRun) {
        Write-Host "DRY RUN passed for prepared commit $ReleaseCommit; publication has not run."
        exit 0
    }

    & git tag $Tag $ReleaseCommit
    if ($LASTEXITCODE -ne 0) { throw 'Tag creation failed; no push attempted' }
    if ((Read-Git -GitArguments @('rev-parse', '--verify', "refs/tags/$Tag^{commit}")) -ne $ReleaseCommit) {
        throw 'Local release tag points at an unexpected commit'
    }
    & git push --atomic origin "${ReleaseCommit}:refs/heads/main" "${ReleaseCommit}:refs/tags/$Tag"
    if ($LASTEXITCODE -ne 0) { throw 'Atomic publication failed; retain the local tag and inspect remote state before retrying' }
    $Published = Read-Git -GitArguments @('ls-remote', '--refs', 'origin', 'refs/heads/main', "refs/tags/$Tag")
    Assert-Contract @{kind='refs'; branch=$Branch; head=$ReleaseCommit; main=$MainCommit; remote=$Published; tag=$Tag}
    Write-Host "Release $Tag verified at $ReleaseCommit on origin main and tag."
} catch {
    Write-Error "Release blocked: $($_.Exception.Message)"
    exit 1
}
