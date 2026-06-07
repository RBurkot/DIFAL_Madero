# DIFAL Indústria — Madero

Geração automática de planilhas DIFAL para a operação Indústria (filial `01GDIN0004`).

## Pipeline

```text
Extrato BI  →  [001] Apuração DIFAL  →  [002] INDUSTRIA-IMPORTAÇÃO  →  ERP
                     ↑                          ↑
              difal-apuracao              difal-importacao
                     └──────── [003] Interface desktop (Python) ────┘
```

## Instalação

```powershell
cd c:\ProjetosIA\DIFAL_Madero
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

## Interface desktop (003) — recomendado

```powershell
difal-desktop
```

Interface gráfica em **Python/Tkinter** para:

- Selecionar arquivos BI e/ou DIFAL
- Informar período e corte
- Acompanhar etapas (validação → apuração → importação → reconciliação)
- Abrir a planilha gerada e a pasta de saída

### Gerar executável autosuficiente (.exe)

```powershell
.\scripts\build-exe.ps1
```

Saída: `dist\DIFAL-Madero.exe` (one-file, sem console).

**Distribuição:** copie o `.exe` para a máquina do usuário. Para SB1, SFT e reconciliação, coloque a planilha de referência (`*28*.xlsx`) na **mesma pasta do executável** ou selecione-a na interface.

Configs (`apuracao.yaml`, `importacao.yaml`, etc.) ficam embutidas no executável.

## CLI — Apuração DIFAL (001)

```powershell
difal-apuracao "DIFAL INDUSTRIA BI.xlsx" --periodo 05/2026 --corte-dia 28 -o output\apuracao.xlsx
```

## CLI — INDUSTRIA-IMPORTAÇÃO (002)

```powershell
difal-importacao "output\apuracao.xlsx" `
  --reconciliar "Cálculo DIFAL Industria até dia 28.xlsx" `
  -o output\importacao.xlsx
```

## API web (opcional, desenvolvimento)

```powershell
pip install -e ".[web]"
.\scripts\start-app.ps1
```

Abre `http://127.0.0.1:8765` (FastAPI + HTML estático legado).

## Specs

- `specs/001-auto-difal-industria/`
- `specs/002-industria-importacao/`
- `specs/003-difal-frontend/`

## Referências

Planilhas baseline no repositório: `DIFAL INDUSTRIA BI.xlsx`, `Cálculo DIFAL Industria até dia 28.xlsx`.
