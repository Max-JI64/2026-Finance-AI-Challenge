$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
& 'C:\Program Files\Python313\python.exe' -m src.data.build_re_stage5_baseline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
