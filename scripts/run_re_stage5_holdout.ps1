param(
    [switch]$DryRun,
    [switch]$Status,
    [switch]$ConfirmOpenHoldout
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$SelectedModes = @($DryRun, $Status, $ConfirmOpenHoldout) | Where-Object { $_ }
if ($SelectedModes.Count -ne 1) {
    throw 'Choose exactly one: -DryRun, -Status, or -ConfirmOpenHoldout.'
}

$Arguments = @('-m', 'src.models.run_re_stage5_holdout')
if ($DryRun) {
    $Arguments += '--dry-run'
}
elseif ($Status) {
    $Arguments += '--status'
}
else {
    $Arguments += @(
        '--run',
        '--confirm-selected-model', 'lightgbm',
        '--confirm-open-holdout'
    )
}

& 'C:\Program Files\Python313\python.exe' @Arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
