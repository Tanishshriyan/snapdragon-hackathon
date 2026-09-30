[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venvDirectory = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvDirectory "Scripts\python.exe"
$pythonCommand = Get-Command python -ErrorAction Stop

Set-Location -LiteralPath $projectRoot

$pythonVersionText = (& $pythonCommand.Source --version 2>&1).ToString()
if ($LASTEXITCODE -ne 0) {
    throw "Could not execute Python."
}

if ($pythonVersionText -notmatch "Python\s+(\d+)\.(\d+)") {
    throw "Could not determine the installed Python version from: $pythonVersionText"
}

$pythonMajor = [int]$Matches[1]
$pythonMinor = [int]$Matches[2]
if (($pythonMajor -lt 3) -or (($pythonMajor -eq 3) -and ($pythonMinor -lt 11))) {
    throw "Doppel requires Python 3.11 or newer. Found: $pythonVersionText"
}

Write-Host "Using $pythonVersionText"

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating virtual environment at $venvDirectory"
    & $pythonCommand.Source -m venv $venvDirectory
    if ($LASTEXITCODE -ne 0) {
        throw "Virtual environment creation failed."
    }
}

if (-not $SkipInstall) {
    Write-Host "Installing runtime dependencies"
    & $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Runtime dependency installation failed."
    }

    Write-Host "Installing development dependencies"
    & $venvPython -m pip install -r (Join-Path $projectRoot "requirements-dev.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Development dependency installation failed."
    }
}

Write-Host "Initializing the local SQLite database"
& $venvPython -c "from app.config.settings import Settings; from app.database.engine import create_database_engine; from app.database.migrations import initialize_database; settings=Settings.from_environment(); settings.ensure_directories(); initialize_database(create_database_engine(settings.database_path)); print(settings.database_path)"
if ($LASTEXITCODE -ne 0) {
    throw "Database initialization failed."
}

Write-Host "Setup complete. Run .\scripts\run.ps1 to start Doppel."
