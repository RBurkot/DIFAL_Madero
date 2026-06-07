# Implementation Plan: Frontend de Seleção de Arquivos e Acompanhamento de Processamento

**Branch**: `003-difal-frontend` | **Date**: 2026-06-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-difal-frontend/spec.md`

## Summary

Interface web local para analistas fiscal/contábil selecionarem arquivos Excel de
entrada, configurarem o período de apuração, executarem o pipeline DIFAL completo
(apuração + INDUSTRIA-IMPORTAÇÃO + reconciliação) e acompanharem o progresso até
o download das planilhas geradas.

Abordagem: **aplicação local** com **backend FastAPI** (orquestração dos motores
Python das features 001/002) e **frontend React (Vite)** servido estaticamente
pelo mesmo processo. Progresso em tempo real via **Server-Sent Events (SSE)**.
Execuções e artefatos persistidos em disco em `data/jobs/{job_id}/`.

## Technical Context

**Language/Version**: Python 3.11+ (API), TypeScript 5.x (frontend)

**Primary Dependencies**:
- Backend: FastAPI, uvicorn, pydantic, sse-starlette (ou StreamingResponse SSE)
- Frontend: React 18, Vite, TanStack Query (opcional), componentes UI leves
- Motores: pacotes `difal_apuracao` (001, futuro) e `difal_importacao` (002)

**Storage**: Filesystem local — `data/uploads/`, `data/jobs/{id}/output/`,
`data/jobs/{id}/job.json` (estado); sem banco de dados na v1

**Testing**: pytest (API + orquestrador), Vitest + Testing Library (componentes
críticos), teste E2E manual via quickstart

**Target Platform**: Windows 10+ (localhost `http://127.0.0.1:8765`); intranet
opcional na mesma máquina/rede interna

**Project Type**: Web app local (backend + frontend)

**Performance Goals**: Upload + validação < 10s; atualização de status SSE < 5s
após mudança de etapa; download disponível < 10s após conclusão

**Constraints**: Offline; um job ativo por instância; dados fiscais não em logs;
CORS restrito a localhost; UI em português

**Scale/Scope**: 1–5 usuários simultâneos na intranet local; ~1 job/minuto no
pico; arquivos até 50 MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Precisão Fiscal | UI delega cálculos aos motores 001/002 sem reprocessar valores? | [x] |
| II. Planilha como Entregável | Download entrega `.xlsx` com abas esperadas? | [x] |
| III. Rastreabilidade | Job ID, histórico de etapas e relatório de reconciliação expostos? | [x] |
| IV. Validação contra Referência | Status de reconciliação reflete motor (aprovado/reprovado)? | [x] |
| V. Simplicidade | FastAPI + React local vs. Electron/cloud — justificado abaixo? | [x] |

**Resultado**: [x] Aprovado para Phase 0  /  [ ] Bloqueado — violações em Complexity Tracking

**Nota pós-design**: Frontend é camada fina; regras fiscais permanecem nos
pacotes Python. Complexidade de SPA justificada por UX de progresso e seleção
de arquivos superior a CLI para usuários de negócio.

## Project Structure

### Documentation (this feature)

```text
specs/003-difal-frontend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-rest.md
│   ├── sse-events.md
│   └── ui-screens.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── difal_api/
│       ├── __init__.py
│       ├── main.py              # FastAPI app, CORS, static mount
│       ├── routes/
│       │   ├── jobs.py          # POST /jobs, GET /jobs/{id}
│       │   ├── uploads.py       # POST /uploads, validação
│       │   └── downloads.py     # GET /jobs/{id}/download/{artifact}
│       ├── services/
│       │   ├── orchestrator.py  # Pipeline 001 → 002 → reconciliação
│       │   ├── validator.py     # Valida layout BI/DIFAL
│       │   └── job_store.py     # Persistência job.json
│       ├── models/
│       │   └── job.py           # Pydantic: Job, Step, Result
│       └── sse.py               # Eventos de progresso
├── pyproject.toml
└── tests/
    ├── test_orchestrator.py
    └── test_jobs_api.py

frontend/
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── HomePage.tsx         # Seleção arquivos + período
│   │   ├── ProcessingPage.tsx   # Stepper + SSE
│   │   └── ResultPage.tsx       # Resumo + download
│   ├── components/
│   │   ├── FilePicker.tsx
│   │   ├── PeriodForm.tsx
│   │   ├── PipelineStepper.tsx
│   │   └── JobHistory.tsx
│   ├── hooks/
│   │   └── useJobEvents.ts      # SSE client
│   └── api/
│       └── client.ts            # REST calls
├── package.json
└── vite.config.ts

data/                            # gitignored
├── uploads/
└── jobs/

scripts/
└── start-app.ps1                # Sobe backend + abre browser
```

**Structure Decision**: Monorepo com `backend/` e `frontend/` separados.
Orquestrador importa motores `difal_apuracao` e `difal_importacao` quando
disponíveis; até lá, stubs com mensagem clara ou subprocess nos CLIs planejados.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| SPA React + FastAPI (2 projetos) | Progresso SSE, UX multi-etapas, histórico | Streamlit/NiceGUI: menos controle de UX e testes; CLI: usuário de negócio não adota |
