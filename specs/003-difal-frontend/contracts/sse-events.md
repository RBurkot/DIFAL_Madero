# SSE Events Contract: Job Progress

**Endpoint**: `GET /api/v1/jobs/{id}/events`

**Headers**: `Accept: text/event-stream`

## Event Types

### `step_started`

```json
{
  "event": "step_started",
  "job_id": "uuid",
  "step_id": "apuracao_difal",
  "label": "Apuração DIFAL",
  "timestamp": "2026-06-07T14:30:00Z"
}
```

### `step_progress`

Emitido a cada batch ou a cada N linhas processadas.

```json
{
  "event": "step_progress",
  "job_id": "uuid",
  "step_id": "apuracao_difal",
  "progress_pct": 45,
  "metrics": {
    "linhas_processadas": 156,
    "total_linhas": 346
  }
}
```

### `step_completed`

```json
{
  "event": "step_completed",
  "job_id": "uuid",
  "step_id": "apuracao_difal",
  "message": "346 linhas apuradas"
}
```

### `step_failed`

```json
{
  "event": "step_failed",
  "job_id": "uuid",
  "step_id": "importacao",
  "error_summary": "Conta contábil inválida na linha 42",
  "recoverable": false
}
```

### `job_completed`

```json
{
  "event": "job_completed",
  "job_id": "uuid",
  "result": {
    "linhas_processadas": 346,
    "lancamentos_gerados": 196,
    "reconciliacao_status": "APROVADO",
    "artifacts": ["difal_workbook", "importacao_workbook"]
  }
}
```

## Client Behavior

- Reconectar automaticamente em caso de queda (EventSource nativo)
- Atualizar stepper e contadores a cada `step_progress`
- Redirecionar para ResultPage em `job_completed` ou exibir erro em `step_failed`
- Timeout de inatividade: 60s sem eventos → polling fallback `GET /jobs/{id}`
