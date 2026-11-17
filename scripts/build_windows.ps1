# Builds dist\StockFih\StockFih.exe. Run from the project root:
#   powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
# -Console keeps a terminal window open next to the app, to see startup errors.
param([switch]$Console)

$ErrorActionPreference = "Stop"

uv run python scripts\make_icon.py
if ($LASTEXITCODE -ne 0) { throw "Icon step failed." }

$mode = if ($Console) { "--console" } else { "--windowed" }
uv run pyinstaller --noconfirm --clean $mode --name StockFih --icon build\stockfih.ico `
    --paths src --add-data "src\stockfih\resources;stockfih\resources" src\stockfih\main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }

Write-Host "Done: dist\StockFih\StockFih.exe"