# Repo Studio Windows per-user installer; no admin rights required.
# Install: powershell -NoProfile -File .\install_windows.ps1 -Repository 'C:\path\to\git\repo'
# Rollback: powershell -NoProfile -File .\install_windows.ps1 -Rollback
[CmdletBinding()]
param([string]$Repository, [switch]$Rollback)
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'Programs\RepoStudio'
$backup = Join-Path $env:LOCALAPPDATA 'RepoStudio\backup\previous-release'
$config = Join-Path $env:APPDATA 'repo-studio\launch.json'
$source = $PSScriptRoot
if (-not $env:LOCALAPPDATA -or -not $env:APPDATA) { throw 'Windows LOCALAPPDATA and APPDATA are required' }
if ($Rollback) {
    if (-not (Test-Path -LiteralPath $backup -PathType Container)) { throw 'No previous-release backup found; nothing changed.' }
    $staged = "$base.rollback-$(Get-Random)"
    if (Test-Path -LiteralPath $base) { Move-Item -LiteralPath $base -Destination $staged }
    try { Copy-Item -LiteralPath $backup -Destination $base -Recurse -Force }
    catch { if (Test-Path $staged) { Move-Item -LiteralPath $staged -Destination $base }; throw }
    if (Test-Path $staged) { Remove-Item -LiteralPath $staged -Recurse -Force }
    Write-Host "Rollback complete: $base"
    exit 0
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'studio.py'))) { throw 'Run this installer from extracted Repo Studio release.' }
if (-not (Test-Path -LiteralPath (Join-Path $source 'launcher.py'))) { throw 'Missing launcher.py' }
if ($Repository) {
    $Repository = [IO.Path]::GetFullPath($Repository)
    if (-not (Test-Path -LiteralPath $Repository -PathType Container)) { throw "Repository directory missing: $Repository" }
    & git -C $Repository rev-parse --show-toplevel | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'The selected directory is not a Git repository.' }
} elseif (-not (Test-Path -LiteralPath $config)) { throw 'First installation requires -Repository with an absolute Git repository path.' }
# Stage configuration independently of the installed code. A failed install must not
# leave launch.json referencing a new repository with the old application.
$configStage = $null
$configOld = $null
$codeOld = $null
$codeInstalled = $false
$backupCreated = $false
if ($Repository) {
    $configDir = Split-Path $config -Parent
    New-Item -ItemType Directory -Force -Path $configDir | Out-Null
    $settings = if (Test-Path -LiteralPath $config) { Get-Content -Raw -LiteralPath $config | ConvertFrom-Json } else { [pscustomobject]@{} }
    $settings | Add-Member -NotePropertyName repo -NotePropertyValue $Repository -Force
    $configStage = Join-Path $configDir ("launch.json.staging-" + [guid]::NewGuid().ToString('N'))
    [IO.File]::WriteAllText($configStage, ($settings | ConvertTo-Json -Depth 8), (New-Object System.Text.UTF8Encoding($false)))
}
$parent = Split-Path $base -Parent
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$staging = "$base.staging-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Force -Path $staging | Out-Null
try {
    $files = @('analysis.py','launcher.py','studio.py','workspace.py','workspace_backup.py','launch_windows.cmd','LICENSE','README.md','USER_GUIDE.md')
    foreach ($name in $files) { Copy-Item -LiteralPath (Join-Path $source $name) -Destination $staging -Force -ErrorAction Stop }
    Copy-Item -LiteralPath (Join-Path $source 'static') -Destination $staging -Recurse -ErrorAction Stop
    if (Test-Path -LiteralPath $base) {
        New-Item -ItemType Directory -Force -Path (Split-Path $backup -Parent) | Out-Null
        if (Test-Path -LiteralPath $backup) { throw "Existing rollback backup found at $backup; archive it before installing again." }
        $backupStage = "$backup.staging-$([guid]::NewGuid().ToString('N'))"
        try {
            Copy-Item -LiteralPath $base -Destination $backupStage -Recurse -ErrorAction Stop
            Move-Item -LiteralPath $backupStage -Destination $backup -ErrorAction Stop
            $backupCreated = $true
        } finally {
            if (Test-Path -LiteralPath $backupStage) { Remove-Item -LiteralPath $backupStage -Recurse -Force }
        }
        $codeOld = "$base.old-$([guid]::NewGuid().ToString('N'))"
        Move-Item -LiteralPath $base -Destination $codeOld -ErrorAction Stop
    }
    Move-Item -LiteralPath $staging -Destination $base -ErrorAction Stop
    $codeInstalled = $true
    if ($env:REPO_STUDIO_QA_FAIL_BEFORE_CONFIG_COMMIT -eq '1') { throw 'Injected QA failure before config commit' }
    if ($configStage) {
        if (Test-Path -LiteralPath $config) {
            $configOld = Join-Path (Split-Path $config -Parent) ("launch.json.old-" + [guid]::NewGuid().ToString('N'))
            Move-Item -LiteralPath $config -Destination $configOld -ErrorAction Stop
        }
        Move-Item -LiteralPath $configStage -Destination $config -ErrorAction Stop
    }
    # Only remove the original code after BOTH code and config have been committed.
    if ($codeOld -and (Test-Path -LiteralPath $codeOld)) { Remove-Item -LiteralPath $codeOld -Recurse -Force -ErrorAction SilentlyContinue }
    if ($configOld -and (Test-Path -LiteralPath $configOld)) { Remove-Item -LiteralPath $configOld -Force -ErrorAction SilentlyContinue }
    Write-Host "Installed at: $base"
    Write-Host "Start with: `"$base\launch_windows.cmd`""
    Write-Host "Config: $config"
    Write-Host 'State: %LOCALAPPDATA%\RepoStudio\data (never deleted by installer or rollback)'
} catch {
    # Recover previous code and config on any failed upgrade, including config failures.
    if ($configOld -and (Test-Path -LiteralPath $configOld)) {
        if (Test-Path -LiteralPath $config) { Remove-Item -LiteralPath $config -Force }
        Move-Item -LiteralPath $configOld -Destination $config
    }
    if ($codeInstalled -and (Test-Path -LiteralPath $base)) { Remove-Item -LiteralPath $base -Recurse -Force }
    if ($codeOld -and (Test-Path -LiteralPath $codeOld)) { Move-Item -LiteralPath $codeOld -Destination $base }
    # A failed update must not consume the one permitted rollback slot.
    if ($backupCreated -and (Test-Path -LiteralPath $backup)) { Remove-Item -LiteralPath $backup -Recurse -Force }
    throw
} finally {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Force -Recurse }
    if ($configStage -and (Test-Path -LiteralPath $configStage)) { Remove-Item -LiteralPath $configStage -Force }
}
