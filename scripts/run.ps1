[CmdletBinding()]
param(
    [switch]$NoSetup
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    if ($NoSetup) {
        throw "The virtual environment is missing. Run .\scripts\setup.ps1 first."
    }
    & (Join-Path $PSScriptRoot "setup.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Setup did not complete successfully."
    }
}

Set-Location -LiteralPath $projectRoot
Write-Host "Starting Doppel. Close the desktop window to stop it."
& $venvPython -m app.main
exit $LASTEXITCODE
