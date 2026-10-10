$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw (
        "Este script debe ejecutarse en Windows; PyInstaller no genera "
        "ejecutables Windows desde Linux o macOS."
    )
}

$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & py -3.14 -m venv .venv-build
} else {
    & python -m venv .venv-build
}
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo crear el entorno virtual. Instala Python 3.14 para Windows."
}

$pythonEntorno = Join-Path $raiz ".venv-build\Scripts\python.exe"
& $pythonEntorno -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron actualizar las herramientas de instalación."
}
& $pythonEntorno -m pip install -r requirements-windows-build.txt
if ($LASTEXITCODE -ne 0) {
    throw "No se pudieron instalar las dependencias para Windows."
}

& $pythonEntorno -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name RecetarioCaprichos `
    --add-data "scripts/database.sql;scripts" `
    src/main.py
if ($LASTEXITCODE -ne 0) {
    throw "Falló la creación del ejecutable."
}

Write-Host "Ejecutable creado en: $raiz\dist\RecetarioCaprichos.exe"
