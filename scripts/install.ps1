[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Skill,

    [ValidateSet('all', 'codex', 'claude', 'gemini', 'grok', 'opencode', 'hermes')]
    [string[]]$Target = @('all'),

    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repoRoot "skills\$Skill"

if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
    throw "Skill not found: $source"
}

$installBase = if ($env:SKILLS_BAR_HOME) {
    $env:SKILLS_BAR_HOME
} else {
    [Environment]::GetFolderPath('UserProfile')
}
$destinations = @{
    codex    = Join-Path $installBase '.agents\skills'
    claude   = Join-Path $installBase '.claude\skills'
    gemini   = Join-Path $installBase '.agents\skills'
    grok     = Join-Path $installBase '.agents\skills'
    opencode = Join-Path $installBase '.agents\skills'
    hermes   = Join-Path $installBase '.hermes\skills'
}

$selected = if ($Target -contains 'all') {
    @('codex', 'claude', 'gemini', 'grok', 'opencode', 'hermes')
} else {
    $Target
}

$roots = $selected | ForEach-Object { $destinations[$_] } | Sort-Object -Unique

foreach ($root in $roots) {
    $destination = Join-Path $root $Skill
    if (Test-Path -LiteralPath $destination) {
        if (-not $Force) {
            throw "Destination already exists: $destination. Re-run with -Force to replace it."
        }
        Remove-Item -LiteralPath $destination -Recurse -Force
    }

    New-Item -ItemType Directory -Path $root -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Recurse
    Write-Output "Installed $Skill -> $destination"
}
