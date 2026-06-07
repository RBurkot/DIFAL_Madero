Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -e . -q

Write-Host "Modo API web (legado). Para uso normal: difal-desktop ou dist\DIFAL-Madero.exe"
Write-Host "Iniciando DIFAL Madero em http://127.0.0.1:8765"
Start-Process "http://127.0.0.1:8765"
uvicorn difal_api.main:app --host 127.0.0.1 --port 8765
