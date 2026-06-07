# Workbook I/O Contract: DIFAL → INDUSTRIA-IMPORTAÇÃO

## Input: Aba DIFAL (`DIFAL MM.AAAA`)

**Required columns** (header row 1):

| Column | Type | Required |
|--------|------|----------|
| FORNECEDOR | string | yes |
| ESTADO | string | yes |
| COD FILIAL | string | yes |
| NOTA FISCAL | string | yes |
| CONTA CONTABIL | string | yes |
| COD PRODUTO | string | yes |
| PRODUTO | string | no |
| NCM | string | no |
| COD FISCAL | string | yes |
| VALOR CONTÁBIL | decimal | yes |
| VALOR ICMS COMPLEMENTAR | decimal | yes |
| NOVO DIFAL | decimal | yes |
| AJUSTE | decimal | yes |

**Row rules**: Dados a partir da linha 2; ignorar linhas com `FORNECEDOR` vazio.

## Input: Aba Auxiliar (opcional — `SFT` ou `BI QLVIEW`)

Usada para enriquecer campos ausentes na aba DIFAL.

| Field needed | SFT column | BI QLVIEW column |
|--------------|------------|------------------|
| chave (derivada) | Nota Fiscal + Cd. Forn + Cd Produto | Nota Fiscal + Cod Fornecedor + Cód Produto |
| nome_fornecedor | Nm Forn | Fornecedor |
| loja | Lj. Forn | Loja |
| data_emissao | Dt Emissao | — |
| data_entrada | Dt Entrada | MES_ANO_ENTRADA |

**Lookup key**: `str(int(nota)) + str(fornecedor) + str(produto)`

## Output: Aba `INDUSTRIA-IMPORTAÇÃO`

**Layout** (conforme referência):

| Row | Content |
|-----|---------|
| 1 | Vazia |
| 2 | Totais consolidados (colunas G–J: valor nota, DIFAL, novo DIFAL, ajuste) |
| 3 | Vazia / metadados auxiliares |
| 4 | Cabeçalho de colunas |
| 5+ | Lançamentos |

**Output columns** (row 4 header):

| # | Column | Source |
|---|--------|--------|
| A | LOJA | lookup / `0001` |
| B | NOTA | int(nota_fiscal) |
| C | NOME FORNE | lookup |
| D | COD FORNECEDOR | FORNECEDOR |
| E | PRODUTO | COD PRODUTO |
| F | CFOP | COD FISCAL |
| G | VALOR DA NOTA | VALOR CONTÁBIL |
| H | DIFAL | VALOR ICMS COMPLEMENTAR |
| I | NOVO DIFAL | NOVO DIFAL |
| J | AJUSTE | AJUSTE |
| K | Chave | derivada |
| L | DATA EMISSAO | lookup |
| M | DATA ENTRADA | lookup |
| N | FILIAL | `01GDIN0004` |
| O | DÉBITO | regra sinal ajuste |
| P | CENTRO DE CUSTO | `290001` |
| Q | COD ITEM CONTABIL | lookup opcional |
| R | COD FORNECEDOR | `F{cod}{loja}` |
| S | CRÉDITO | regra sinal ajuste |
| T | CENTRO DE CUSTO | `290001` |
| U | COD ITEM CONTABIL | lookup opcional |
| V | COD FORNECEDOR | `F{cod}{loja}` |
| W | VALOR | abs(ajuste) |
| X | HISTÓRICO | `{nota}-{nome}` truncado |
| Y | JUSTIFICATIVA | `AJUSTE FISCAL DIFAL MM.AAAA` |
| Z | DATA EMISSÃO | = DATA EMISSAO |
| AA | DATA CONTABILIZAÇÃO | = DATA ENTRADA |

## Transformation Rules

```text
IF abs(ajuste) < limiar: SKIP
IF conta_contabil invalid: EXCEPTION (no row)
IF ajuste > 0:
  debito = conta_contabil; credito = 20140010007
IF ajuste < 0:
  debito = 20140010007; credito = conta_contabil
valor_lancamento = round(abs(ajuste), 2)
chave = str(int(nota)) + fornecedor + cod_produto
```
