Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -e ".[desktop]" -q

Write-Host "Gerando executável DIFAL-Madero.exe ..."
pyinstaller --noconfirm DIFAL-Madero.spec

$exe = "dist\DIFAL-Madero.exe"
if (Test-Path $exe) {
    Write-Host ""
    Write-Host "OK: $((Resolve-Path $exe).Path)"
    Write-Host ""
    Write-Host "Para usar SB1/SFT/reconciliacao, coloque a planilha de referencia"
    Write-Host "(*28*.xlsx) na mesma pasta do executavel ou selecione na interface."
} else {
    Write-Error "Build falhou - verifique a pasta dist"
    exit 1
}
