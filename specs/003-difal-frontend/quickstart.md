# Quickstart: 003-difal-frontend

## Prerequisites

- Python 3.11+, Node.js 20+
- Planilhas de referência no projeto (`DIFAL INDUSTRIA BI.xlsx`, etc.)
- Motores 001/002 implementados ou stubs ativos

## Setup (após implementação)

```powershell
cd c:\ProjetosIA\DIFAL_Madero

# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Frontend
cd ..\frontend
npm install
npm run build
```

## Iniciar aplicação

```powershell
cd c:\ProjetosIA\DIFAL_Madero
.\scripts\start-app.ps1
```

Abre automaticamente `http://127.0.0.1:8765`

## Fluxo de teste manual

1. **Home**: selecionar `DIFAL INDUSTRIA BI.xlsx` → aguardar badge "Válido"
2. Informar período `05/2026`, modo `completo`, corte dia `28`
3. Clicar **Iniciar processamento**
4. **Processing**: verificar stepper avançando (validação → apuração → importação → reconciliação)
5. **Result**: conferir totais, status reconciliação, baixar planilhas
6. Validar abas `DIFAL 05.2026` e `INDUSTRIA-IMPORTAÇÃO` no arquivo baixado

## Modo somente importação

1. Selecionar planilha com aba `DIFAL 05.2026` já apurada
2. Modo `somente_importacao`
3. Verificar que etapa "Apuração DIFAL" aparece como ignorada/concluída instantaneamente

## Desenvolvimento

```powershell
# Terminal 1 — API com reload
cd backend
uvicorn difal_api.main:app --reload --port 8765

# Terminal 2 — Frontend dev
cd frontend
npm run dev
```

## Troubleshooting

| Problema | Ação |
|----------|------|
| Upload inválido | Conferir colunas do BI na spec 001 |
| Job 409 | Aguardar job anterior ou reiniciar app |
| Motor não instalado | Verificar `GET /health` → engines |
| SSE não atualiza | Verificar firewall localhost; fallback GET /jobs/{id} |
