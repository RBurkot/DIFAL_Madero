# Research: 002-industria-importacao

**Date**: 2026-06-07 | **Feature**: Geração Automática da Planilha INDUSTRIA-IMPORTAÇÃO

## R1 — Stack de manipulação Excel

**Decision**: Python 3.11+ com `openpyxl` para leitura e escrita.

**Rationale**: O projeto já usa `openpyxl` para inspecionar referências; preserva
formatação de células, tipos de data e controle fino de layout (linhas de totais
no topo, cabeçalho na linha 4 da referência). Adequado para planilha como
entregável primário (Constituição II).

**Alternatives considered**:
- `pandas` + `openpyxl`: melhor para análise, pior para layout fiel linha a linha.
- `xlwings`: depende de Excel instalado; rejeitado por portabilidade CI.
- VBA/macros: difícil versionar e testar; rejeitado por governança.

## R2 — Interface de execução

**Decision**: CLI `difal-importacao` via `typer` com subcomando `gerar`.

**Rationale**: Alinha com perfil offline/local, simples de invocar no PowerShell,
testável e compatível com pipeline futuro (feature 001 → 002 encadeada).

**Alternatives considered**:
- Script `.ps1` puro: sem tipagem/validação estruturada.
- Interface web: over-engineering para usuário único (analista fiscal).

## R3 — Enriquecimento de dados ausentes na aba DIFAL

**Decision**: Leitura opcional de abas auxiliares no mesmo workbook (`SFT`,
`BI QLVIEW`) indexadas por chave `{nota}{fornecedor}{produto}` para obter
`NOME FORNE`, `DATA EMISSAO`, `DATA ENTRADA` e `LOJA`.

**Rationale**: A aba `DIFAL 05.2026` da referência **não contém** nome do
fornecedor nem datas; a aba `INDUSTRIA-IMPORTAÇÃO` **exige** esses campos. A
aba `SFT` no mesmo arquivo traz `Nm Forn`, `Dt Emissao`, `Dt Entrada`, `Lj. Forn`
e permite compor a chave via nota + fornecedor + produto.

**Alternatives considered**:
- Exigir que feature 001 inclua todos os campos na aba DIFAL: válido a médio
  prazo, mas bloqueia 002 antes de 001 estar pronta; mitigado com lookup opcional.
- CSV externo de fornecedores: mais um artefato manual; rejeitado como padrão.

## R4 — Regra de elegibilidade (materialidade)

**Decision**: Incluir linha se `abs(ajuste) >= limiar` (padrão R$ 0,01),
configurável em `config/importacao.yaml`.

**Rationale**: Análise da referência 05/2026: 346 linhas DIFAL, 336 com ajuste ≠ 0,
196 lançamentos importados; 127 excluídos são microajustes (|ajuste| < 0,01).

**Alternatives considered**:
- Incluir todo ajuste ≠ 0: geraria 140 lançamentos a mais com ruído contábil.
- Limiar R$ 1,00: excluiria lançamentos válidos na referência (ex.: R$ 0,006 ainda
  aparece em alguns casos — revalidar na implementação com tolerância configurável).

## R5 — Regra débito/crédito

**Decision**:
- Ajuste > 0: débito = `CONTA CONTABIL` (DIFAL), crédito = `20140010007`.
- Ajuste < 0: débito = `20140010007`, crédito = `CONTA CONTABIL`.
- Valor lançamento = `round(abs(ajuste), 2)`.

**Rationale**: Confirmado em amostras da referência (notas 13, 190054, 34507).

**Alternatives considered**:
- Sempre débito na conta contábil: incorreto para ajustes negativos.

## R6 — Composição de chave e histórico

**Decision**:
- Chave: `str(int(nota_fiscal)) + str(fornecedor) + str(cod_produto)` sem padding.
- Histórico: `"{nota}-{nome_fornecedor}"` truncado a 28 caracteres.
- Justificativa: `AJUSTE FISCAL DIFAL {MM.AAAA}` extraído do nome da aba DIFAL.

**Rationale**: 196/196 chaves da referência 05/2026 casam com DIFAL usando essa fórmula.

## R7 — Estratégia de validação

**Decision**: Teste de integração compara saída gerada vs. aba referência
`INDUSTRIA-IMPORTAÇÃO` por chave (débito, crédito, valor); relatório JSON/CSV de
reconciliação emitido em toda execução.

**Rationale**: Atende Constituição III e IV; bloqueia regressões antes de entrega.

**Alternatives considered**:
- Validação manual apenas: não escalável mensalmente.

## R8 — Dependência da feature 001

**Decision**: 002 aceita qualquer aba `DIFAL MM.AAAA` compatível com o schema
documentado em `contracts/workbook-io.md`; feature 001 é produtora preferencial,
não bloqueante se referência manual for fornecida.

**Rationale**: Permite desenvolvimento e testes paralelos usando planilha de
referência existente.
