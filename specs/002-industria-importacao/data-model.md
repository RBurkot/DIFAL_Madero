# Data Model: 002-industria-importacao

## Entity Relationship Overview

```text
PeriodoApuracao 1 ── * LinhaApuracaoDifal
LinhaApuracaoDifal 0..1 ── 1 LancamentoImportacao (se elegível)
PeriodoApuracao 1 ── 1 TotaisConsolidados
ExecucaoGeracao 1 ── 1 RelatorioReconciliacao
FornecedorLookup * ── * LinhaApuracaoDifal (enriquecimento opcional)
```

## Entities

### PeriodoApuracao

| Field | Type | Rules |
|-------|------|-------|
| mes | int (1-12) | Extraído do nome da aba `DIFAL MM.AAAA` |
| ano | int | Extraído do nome da aba |
| label | string | Ex.: `05.2026` |
| filial | string | Padrão `01GDIN0004` |
| aba_origem | string | Nome exato da aba DIFAL |

**Validation**: Nome da aba MUST corresponder ao padrão `^DIFAL\s+\d{2}\.\d{4}\s*$`.

### LinhaApuracaoDifal

Origem: aba `DIFAL MM.AAAA`, uma linha por item de nota.

| Field | Type | Source Column (DIFAL) |
|-------|------|----------------------|
| fornecedor_cod | string | FORNECEDOR |
| uf_origem | string | ESTADO |
| filial_cod | string | COD FILIAL |
| nota_fiscal | string | NOTA FISCAL |
| conta_contabil | string | CONTA CONTABIL |
| cod_produto | string | COD PRODUTO |
| produto_desc | string | PRODUTO |
| ncm | string | NCM |
| cfop | string | COD FISCAL |
| valor_contabil | decimal | VALOR CONTÁBIL |
| valor_icms_complementar | decimal | VALOR ICMS COMPLEMENTAR |
| novo_difal | decimal | NOVO DIFAL |
| ajuste | decimal | AJUSTE |

**Validation**:
- `conta_contabil` MUST NOT ser `#N/A`, vazio ou não numérico para elegibilidade.
- `ajuste` MAY ser negativo, positivo ou zero.
- `cfop` MUST ser `2551` ou `2556` no escopo atual (outros → exceção sinalizada).

**Computed**:
- `chave_rastreio` = `int(nota_fiscal)` + `fornecedor_cod` + `cod_produto` (strings)
- `elegivel` = `abs(ajuste) >= limiar_materialidade`

### FornecedorLookup (enriquecimento opcional)

Origem: aba `SFT` ou `BI QLVIEW`, index por `chave_rastreio`.

| Field | Type | Source |
|-------|------|--------|
| chave_rastreio | string | derivada ou CHAVE |
| nome_fornecedor | string | Nm Forn / Fornecedor |
| loja | string | Lj. Forn / Loja (padrão `0001`) |
| data_emissao | date | Dt Emissao / DATA EMISSAO |
| data_entrada | date | Dt Entrada / MES_ANO_ENTRADA |

**Validation**: Campos ausentes não bloqueiam geração; lançamento marcado
`pendente_enriquecimento=true`.

### LancamentoImportacao

Destino: aba `INDUSTRIA-IMPORTAÇÃO`.

| Field | Type | Rules |
|-------|------|-------|
| loja | string | Lookup ou `0001` |
| nota | int/string | Sem zeros à esquerda na exibição |
| nome_fornecedor | string | Lookup; histórico truncado |
| cod_fornecedor | string | = fornecedor_cod |
| produto | string | = cod_produto |
| cfop | string | = cfop da linha DIFAL |
| valor_nota | decimal | = valor_contabil |
| difal | decimal | = valor_icms_complementar |
| novo_difal | decimal | = novo_difal |
| ajuste | decimal | = ajuste (sinal preservado) |
| chave | string | = chave_rastreio |
| data_emissao | date | Lookup |
| data_entrada | date | Lookup |
| filial | string | `01GDIN0004` |
| debito | string | Conta contábil ou `20140010007` |
| credito | string | `20140010007` ou conta contábil |
| centro_custo | string | `290001` |
| cod_item_contabil | string | Opcional; do lookup SB1 se disponível |
| cod_fornecedor_debito | string | `F{cod}{loja}` |
| cod_fornecedor_credito | string | `F{cod}{loja}` |
| valor_lancamento | decimal | `round(abs(ajuste), 2)` |
| historico | string | `{nota}-{nome}` max 28 chars |
| justificativa | string | `AJUSTE FISCAL DIFAL {MM.AAAA}` |
| data_contabilizacao | date | = data_entrada quando disponível |

**State transitions**:

```text
LinhaApuracaoDifal
  ├─ ajuste == 0 ──────────────────────► ignorada
  ├─ abs(ajuste) < limiar ─────────────► excluida_materialidade
  ├─ conta_contabil invalida ──────────► excecao (sem lançamento)
  └─ elegivel + conta valida ──────────► LancamentoImportacao
         ├─ ajuste > 0 → debito=conta, credito=20140010007
         └─ ajuste < 0 → debito=20140010007, credito=conta
```

### TotaisConsolidados

Linha de cabeçalho (linha 2 da referência) agregando lançamentos elegíveis.

| Field | Type | Aggregation |
|-------|------|-------------|
| total_valor_nota | decimal | SUM(valor_nota) |
| total_difal | decimal | SUM(difal) |
| total_novo_difal | decimal | SUM(novo_difal) |
| total_ajuste | decimal | SUM(ajuste) |

**Note**: Totais da referência 05/2026 incluem universo maior que só lançamentos
(importados); implementação MUST documentar se totais são sobre elegíveis ou
universo DIFAL completo — **decisão**: totais sobre **todas as linhas DIFAL com
ajuste ≠ 0** (alinha referência linha 2: 2.985.957,59 / 573.121,73).

### RelatorioReconciliacao

| Field | Type | Description |
|-------|------|-------------|
| periodo | string | MM.AAAA |
| linhas_difal_total | int | Linhas lidas |
| linhas_ajuste_nao_zero | int | Com ajuste ≠ 0 |
| linhas_elegiveis | int | Passaram materialidade |
| lancamentos_gerados | int | Escritos na aba |
| excluidas_materialidade | int | |
| excecoes_conta_invalida | int | |
| pendencias_enriquecimento | int | Sem nome/data |
| divergencias_referencia | list | Chave + campo + esperado + obtido |

### ConfiguracaoImportacao (`config/importacao.yaml`)

| Field | Default | Description |
|-------|---------|-------------|
| limiar_materialidade | 0.01 | Mínimo \|ajuste\| para lançamento |
| conta_icms_recolher | 20140010007 | Contrapartida padrão |
| centro_custo | 290001 | Fixo |
| filial | 01GDIN0004 | Escopo |
| historico_max_len | 28 | Truncamento |
| tolerancia_linha | 0.01 | Reconciliação |
| tolerancia_total | 1.00 | Totais consolidados |
