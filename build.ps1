# build.ps1 - empaqueta la app con PyInstaller en un solo .exe
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

& $python -m PyInstaller --clean --noconfirm --onefile --windowed `
    --collect-data customtkinter --name "JSConnect-Win-Coverage" main.py
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo construir el ejecutable."
}

Write-Host ""
Write-Host "Listo: dist\JSConnect-Win-Coverage.exe"
