param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8020,
    [switch]$SkipTests,
    [switch]$RecreateVenv,
    [switch]$UpgradePip,
    [switch]$NoStart
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

Set-Location $ProjectRoot

Write-Host "==> Deploying personal-AI-searcher from $ProjectRoot"

if ($RecreateVenv -and (Test-Path $VenvPath)) {
    Write-Host "==> Removing existing virtual environment"
    Remove-Item -LiteralPath $VenvPath -Recurse -Force
}

if (-not (Test-Path $PythonPath)) {
    Write-Host "==> Creating virtual environment"
    python -m venv $VenvPath
}

if ($UpgradePip) {
    Write-Host "==> Upgrading pip"
    & $PythonPath -m pip install --upgrade pip
}

Write-Host "==> Installing dependencies"
& $PythonPath -m pip install -r requirements.txt

Write-Host "==> Initializing database"
& $PythonPath -m app.db.init_db

if (-not $SkipTests) {
    Write-Host "==> Running tests"
    & $PythonPath -m pytest
}

if ($NoStart) {
    Write-Host "==> Deployment finished. Service was not started because -NoStart was set."
    exit 0
}

Write-Host "==> Starting service at http://$HostAddress`:$Port"
& $PythonPath -m uvicorn app.main:app --host $HostAddress --port $Port
