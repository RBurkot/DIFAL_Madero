# Reconciliation Report Contract

## File Format

JSON (UTF-8), gerado em toda execução com `--reconciliar` ou por padrão em `relatorio/`.

## Schema

```json
{
  "meta": {
    "feature": "002-industria-importacao",
    "periodo": "05.2026",
    "gerado_em": "2026-06-07T14:30:00",
    "entrada": "path/to/workbook.xlsx",
    "saida": "path/to/output.xlsx",
    "referencia": "path/to/reference.xlsx"
  },
  "contagens": {
    "linhas_difal_total": 346,
    "linhas_ajuste_nao_zero": 336,
    "linhas_elegiveis": 203,
    "lancamentos_gerados": 196,
    "excluidas_materialidade": 127,
    "excecoes_conta_invalida": 3,
    "pendencias_enriquecimento": 5
  },
  "totais": {
    "valor_nota": { "gerado": 2985957.59, "referencia": 2985957.59, "delta": 0.0 },
    "difal": { "gerado": 573121.73, "referencia": 573121.73, "delta": 0.0 },
    "novo_difal": { "gerado": 573216.20, "referencia": 573216.20, "delta": 0.0 },
    "ajuste": { "gerado": 94.47, "referencia": 94.47, "delta": 0.0 }
  },
  "divergencias": [
    {
      "chave": "14957720003310724652001700",
      "campo": "valor_lancamento",
      "esperado": 0.01,
      "obtido": 0.00,
      "delta": -0.01,
      "dentro_tolerancia": true
    }
  ],
  "chaves_ausentes_referencia": [],
  "chaves_extras_geradas": [],
  "resultado": "APROVADO"
}
```

## Resultado

| Value | Condition |
|-------|-----------|
| `APROVADO` | Zero divergências acima de `tolerancia_linha`; totais dentro de `tolerancia_total` |
| `APROVADO_COM_RESSALVAS` | Divergências apenas em campos não numéricos (nome truncado, datas) |
| `REPROVADO` | Qualquer divergência numérica acima da tolerância em amostra obrigatória |

## Mandatory Test Sample (05/2026)

196 chaves presentes na aba `INDUSTRIA-IMPORTAÇÃO` da referência MUST ser
comparadas campo a campo (`debito`, `credito`, `valor_lancamento`).
