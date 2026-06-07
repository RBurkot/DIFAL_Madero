# Quickstart: 002-industria-importacao

## Prerequisites

- Python 3.11+
- Planilha de entrada com aba `DIFAL MM.AAAA` (ex.: saída da feature 001 ou
  `Cálculo DIFAL Industria até dia 28.xlsx`)
- Opcional: mesma planilha com aba `SFT` para nome do fornecedor e datas

## Setup (após implementação)

```powershell
cd c:\ProjetosIA\DIFAL_Madero
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Gerar INDUSTRIA-IMPORTAÇÃO

```powershell
difal-importacao gerar `
  "C:\ProjetosIA\DIFAL_Madero\Cálculo DIFAL Industria até dia 28.xlsx" `
  --aba-difal "DIFAL 05.2026 " `
  --aba-auxiliar "SFT " `
  --saida ".\output\industria-importacao-052026.xlsx" `
  --reconciliar "C:\ProjetosIA\DIFAL_Madero\Cálculo DIFAL Industria até dia 28.xlsx"
```

## Validar resultado

1. Abrir `output\industria-importacao-052026.xlsx` → aba `INDUSTRIA-IMPORTAÇÃO`
2. Conferir linha 2 (totais) vs. referência
3. Conferir `reconciliacao.json` → `"resultado": "APROVADO"`
4. Amostra manual: nota 13 (ajuste positivo), nota 190054 produto distinto
   (ajuste negativo com inversão débito/crédito)

## Run tests

```powershell
pytest tests/ -v
pytest tests/integration/test_gerar_importacao_052026.py -v
```

## Troubleshooting

| Problema | Ação |
|----------|------|
| Aba DIFAL não encontrada | Passar `--aba-difal` com nome exato (atenção a espaços no final) |
| NOME FORNE vazio | Incluir aba `SFT` ou `BI QLVIEW`; sem ela, histórico usa código |
| Divergência em totais | Verificar se totais são sobre universo DIFAL completo vs. só elegíveis |
| Conta `#N/A` | Corrigir na aba DIFAL (feature 001) antes de regerar importação |

## Pipeline encadeado (futuro)

```text
extrato BI  →  [001] DIFAL MM.AAAA  →  [002] INDUSTRIA-IMPORTAÇÃO  →  ERP
```
