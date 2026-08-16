$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

& 'C:\Program Files\Python313\python.exe' 'scripts\build_re_stage6.py'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& 'C:\Program Files\Python313\python.exe' -m pytest -q 'tests\test_re_stage6.py'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
