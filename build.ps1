# Build PowerModeSwitch.exe
#
#   .\build.ps1
#
# Creates a virtual environment if needed, installs build tools, generates the
# icon, and packages a single-file executable with an administrator manifest.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.11 -m venv .venv
    } else {
        python -m venv .venv
    }
}

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
& $python -m pip install --upgrade pip --quiet
& $python -m pip install -r requirements-dev.txt --quiet

Write-Host "Checking sources..." -ForegroundColor Cyan
& $python -m py_compile power_mode.py gui.py tools\make_icon.py

Write-Host "Generating icon..." -ForegroundColor Cyan
& $python tools\make_icon.py

Write-Host "Packaging executable..." -ForegroundColor Cyan
& $python -m PyInstaller --noconfirm --clean PowerModeSwitch.spec

$exe = Join-Path $PSScriptRoot "dist\PowerModeSwitch.exe"
if (Test-Path $exe) {
    $size = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Built $exe ($size MB)" -ForegroundColor Green
    Write-Host "Double-click it to launch - Windows will ask for administrator rights."
} else {
    Write-Error "Build failed: $exe not found"
    exit 1
}
