# Research: 003-difal-frontend

**Date**: 2026-06-07 | **Feature**: Frontend DIFAL

## R1 — Arquitetura da aplicação

**Decision**: Web app local — FastAPI (backend) + React/Vite (frontend).

**Rationale**: Usuários Windows já têm browser; evita instalar Electron; backend
Python reutiliza motores 001/002; SSE nativo para progresso sem WebSocket
complexo; deploy intranet = mesma máquina servindo API + static files.

**Alternatives considered**:
- **Electron**: bundle pesado; duplica runtime.
- **Streamlit**: rápido mas UX limitada para stepper multi-etapa e histórico.
- **Tauri + Python sidecar**: bom longo prazo; mais setup inicial.
- **CLI only**: já planejado em 002; insuficiente para spec 003.

## R2 — Comunicação de progresso

**Decision**: Server-Sent Events (`GET /jobs/{id}/events`).

**Rationale**: Unidirecional (servidor → UI), simples, reconexão automática,
adequado para etapas sequenciais com contadores. Atende SC-002 (update < 5s).

**Alternatives considered**:
- **Polling**: mais latência e carga; rejeitado.
- **WebSocket**: bidirecional desnecessário para este fluxo.

## R3 — Upload e seleção de arquivos

**Decision**: Upload via `POST /uploads` (multipart) para `data/uploads/{uuid}/`;
validação imediata retorna `{ valid, type: bi|difal, errors[] }`.

**Rationale**: Browser file picker → upload; funciona em intranet; paths isolados
por UUID evitam colisão. Alternativa path local (input de texto) como fallback
opcional em v1.1 para arquivos em rede UNC.

**Alternatives considered**:
- **Apenas path UNC no form**: falha em sandbox do browser; oferecer como campo
  texto adicional no backend, não no file picker web padrão.

## R4 — Orquestração do pipeline

**Decision**: `JobOrchestrator` executa etapas em thread/background task:

1. `validacao` — validator.py
2. `apuracao_difal` — motor 001 (ou stub)
3. `importacao` — motor 002
4. `reconciliacao` — reconciliation dos motores

Estado persistido em `data/jobs/{id}/job.json` após cada transição.

**Rationale**: Recuperação de sessão; um job ativo (lock file); audit trail
(Constituição III).

**Alternatives considered**:
- **Celery/Redis**: over-engineering para v1 local.
- **Subprocess CLI only**: válido como adapter até motores importáveis.

## R5 — Modos de execução (FR-004)

**Decision**: Três modos expostos na UI:

| Modo | Entrada | Etapas |
|------|---------|--------|
| `completo` | BI `.xlsx` | validação → apuração → importação → reconciliação |
| `somente_importacao` | Planilha com aba DIFAL | validação → importação → reconciliação |
| `somente_apuracao` | BI `.xlsx` | validação → apuração |

**Rationale**: Cobre FR-004 e fluxos das specs 001/002 sem duplicar lógica.

## R6 — Segurança e privacidade (FR-010)

**Decision**:
- Bind `127.0.0.1` por padrão
- Logs sem valores de nota/fornecedor completos
- Erros na UI: mensagem genérica + código de linha (ex.: "linha 42")
- `data/` gitignored

**Rationale**: Dados fiscais sensíveis; ambiente corporativo sem SSO na v1.

## R7 — Dependência dos motores 001/002

**Decision**: Interface `PipelineEngine` com implementações:
- `ImportEngine` → `difal_importacao` (quando existir)
- `ApuracaoEngine` → `difal_apuracao` (quando existir)
- `StubEngine` → retorna erro amigável "motor não instalado" em dev

**Rationale**: Permite desenvolver UI em paralelo; desbloqueia demo de fluxo
com motor 002 primeiro (já planejado).

## R8 — UI/UX

**Decision**: 3 telas — Home (arquivos + período), Processing (stepper + log
resumido), Result (métricas + downloads + alertas). Histórico lateral com
últimas 10 execuções da sessão (localStorage + API).

**Rationale**: Mapeia diretamente US1, US2, US3; português; status cores:
verde/aprovado, amarelo/ressalvas, vermelho/erro.
