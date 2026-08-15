param(
    [switch]$ValidateOnly,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = 'C:\Program Files\Python313\python.exe'

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python executable not found: $pythonExe"
}

Set-Location -LiteralPath $projectRoot

$pythonArguments = @('-u', '-m', 'src.models.run_stage5_final_2025')
if ($ValidateOnly) {
    $pythonArguments += '--validate-only'
}
if ($Status) {
    $pythonArguments += '--status'
}

& $pythonExe @pythonArguments
if ($LASTEXITCODE -ne 0) {
    throw "Stage 5 final 2025 audit failed with exit code $LASTEXITCODE"
}
