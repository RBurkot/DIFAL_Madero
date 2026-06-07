# Data Model: 003-difal-frontend

## Overview

```text
Upload 1 ── * Job 1 ── * PipelineStep
Job 1 ── 1 JobResult
Job 1 ── * Artifact (output files)
Session 1 ── * Job (histórico recente)
```

## Entities

### Upload

| Field | Type | Rules |
|-------|------|-------|
| id | UUID | Gerado no POST /uploads |
| filename | string | Nome original |
| path | string | `data/uploads/{id}/{filename}` |
| type | enum | `bi`, `difal`, `unknown` |
| valid | boolean | Resultado da validação |
| errors | string[] | Mensagens de layout |
| size_bytes | int | |
| uploaded_at | datetime | |

### Job

| Field | Type | Rules |
|-------|------|-------|
| id | UUID | |
| mode | enum | `completo`, `somente_importacao`, `somente_apuracao` |
| periodo | string | `MM/AAAA` |
| corte_dia | int? | Opcional 1–31 |
| status | enum | `pending`, `running`, `completed`, `failed`, `cancelled` |
| upload_ids | UUID[] | BI e/ou DIFAL conforme modo |
| current_step | string | Id da etapa ativa |
| created_at | datetime | |
| finished_at | datetime? | |
| error_summary | string? | Sem dados fiscais completos |

### PipelineStep

| Field | Type | Rules |
|-------|------|-------|
| id | string | `validacao`, `apuracao_difal`, `importacao`, `reconciliacao` |
| label | string | Nome exibido em português |
| status | enum | `pending`, `running`, `completed`, `failed`, `skipped` |
| progress_pct | int | 0–100 |
| metrics | object | Ex.: `{ linhas_processadas, lancamentos_gerados }` |
| started_at | datetime? | |
| finished_at | datetime? | |
| message | string? | Resumo para UI |

### JobResult

| Field | Type | Rules |
|-------|------|-------|
| job_id | UUID | |
| linhas_processadas | int | |
| lancamentos_gerados | int | |
| totais | object | valor_nota, difal, novo_difal, ajuste |
| reconciliacao_status | enum | `APROVADO`, `APROVADO_COM_RESSALVAS`, `REPROVADO` |
| alertas | Alerta[] | |
| artifacts | Artifact[] | |

### Artifact

| Field | Type | Rules |
|-------|------|-------|
| name | string | Ex.: `apuração-052026.xlsx` |
| type | enum | `difal_workbook`, `importacao_workbook`, `reconciliacao_json` |
| path | string | `data/jobs/{id}/output/` |
| size_bytes | int | |

### Alerta

| Field | Type | Rules |
|-------|------|-------|
| tipo | enum | `conta_invalida`, `materialidade`, `enriquecimento`, `periodo_divergente` |
| mensagem | string | Linguagem de negócio |
| referencia | string? | Ex.: "linha 42" — sem CNPJ/valor completo |

### SessionHistory (client-side + API)

| Field | Type | Rules |
|-------|------|-------|
| jobs | JobSummary[] | Últimas 10 execuções |
| stored_in | string | localStorage + `GET /jobs?limit=10` |

## State Machine: Job

```text
pending → running → completed
                 ↘ failed
running → cancelled (opcional v1.1)
```

## State Machine: PipelineStep (within running job)

```text
validacao → apuracao_difal → importacao → reconciliacao
         (skipped se somente_importacao)
apuracao_difal skipped se somente_importacao
```

## API Persistence: job.json schema (simplified)

```json
{
  "id": "uuid",
  "mode": "completo",
  "periodo": "05/2026",
  "status": "running",
  "steps": [
    { "id": "validacao", "status": "completed", "progress_pct": 100 },
    { "id": "apuracao_difal", "status": "running", "progress_pct": 45,
      "metrics": { "linhas_processadas": 156 } }
  ],
  "result": null
}
```
