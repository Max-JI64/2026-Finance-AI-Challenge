param(
    [string]$PythonPath = "C:\Program Files\Python313\python.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$resolvedPython = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($PythonPath)

if (-not (Test-Path -LiteralPath $resolvedPython -PathType Leaf)) {
    throw "Python executable not found: $resolvedPython"
}

Push-Location -LiteralPath $projectRoot
try {
    & $resolvedPython --version
    if ($LASTEXITCODE -ne 0) { throw "Python version check failed." }

    & $resolvedPython -c "import fastapi, httpx, pydantic, pytest, yaml; print('dependency_imports=ok')"
    if ($LASTEXITCODE -ne 0) { throw "Dependency import check failed." }

    & $resolvedPython -m pytest
    if ($LASTEXITCODE -ne 0) { throw "Stage 0 tests failed." }

    Write-Output "stage0_verification=passed"
} finally {
    Pop-Location
}

