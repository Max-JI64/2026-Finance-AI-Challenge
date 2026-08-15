$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& 'C:\Program Files\Python313\python.exe' -m src.models.build_stage6_reference
if ($LASTEXITCODE -ne 0) {
    throw "Stage 6 reference build failed with exit code $LASTEXITCODE"
}

