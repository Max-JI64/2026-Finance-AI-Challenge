param(
    [switch]$DryRun,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$Arguments = @('-m', 'src.models.run_re_stage5_quantile')
if ($DryRun) { $Arguments += '--dry-run' }
elseif ($Status) { $Arguments += '--status' }
else { $Arguments += @('--phase', 'cv') }

& 'C:\Program Files\Python313\python.exe' @Arguments
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
