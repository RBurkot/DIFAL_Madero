# REST API Contract: difal-api

**Base URL**: `http://127.0.0.1:8765/api/v1`

## POST /uploads

Upload de arquivo Excel para validação.

**Request**: `multipart/form-data`
- `file`: arquivo `.xlsx`
- `expected_type` (optional): `bi` | `difal`

**Response 201**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "DIFAL INDUSTRIA BI.xlsx",
  "type": "bi",
  "valid": true,
  "errors": [],
  "size_bytes": 2048576
}
```

**Response 422**: layout inválido (`valid: false`, `errors` preenchido)

## POST /jobs

Inicia processamento.

**Request**:
```json
{
  "mode": "completo",
  "periodo": "05/2026",
  "corte_dia": 28,
  "upload_ids": {
    "bi": "550e8400-e29b-41d4-a716-446655440000",
    "difal": null
  }
}
```

**Response 202**:
```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "pending",
  "mode": "completo",
  "periodo": "05/2026"
}
```

**Response 409**: outro job já em execução

## GET /jobs/{id}

Estado completo do job.

**Response 200**: objeto `Job` com `steps[]` e `result` (se concluído)

## GET /jobs?limit=10

Histórico recente de execuções.

## GET /jobs/{id}/download/{artifact_type}

Download de artefato.

**artifact_type**: `difal_workbook` | `importacao_workbook` | `reconciliacao_json`

**Response 200**: arquivo binário com `Content-Disposition: attachment`

## GET /health

**Response 200**: `{ "status": "ok", "engines": { "apuracao": true, "importacao": false } }`
