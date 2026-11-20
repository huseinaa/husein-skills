# Links skills from this repo into ~/.claude/skills, so a `git pull` updates them.
#   .\install.ps1                      all skills
#   .\install.ps1 reel-edit            one skill
#   .\install.ps1 reel-edit feature-testing
# No admin rights needed: it makes directory junctions.

param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Skills)

$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'skills'
$target = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force -Path $target | Out-Null

$available = Get-ChildItem -Directory $source | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object { $_.Name }
if (-not $Skills -or $Skills.Count -eq 0) { $Skills = $available }

foreach ($name in $Skills) {
    if ($available -notcontains $name) {
        Write-Host "SKIP  $name  (no such skill; available: $($available -join ', '))" -ForegroundColor Yellow
        continue
    }
    $link = Join-Path $target $name
    $from = Join-Path $source $name
    $existing = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
    if ($existing) {
        if ($existing.LinkType) {
            # An old link: replace it. Removing a junction never touches what it points to.
            $existing.Delete()
        } else {
            Write-Host "SKIP  $name  ($link is a real folder; move or delete it first, then run again)" -ForegroundColor Yellow
            continue
        }
    }
    New-Item -ItemType Junction -Path $link -Target $from | Out-Null
    Write-Host "OK    $name  ->  $from" -ForegroundColor Green
}

Write-Host "`nDone. Open a new Claude Code session and type / to see the skills."
