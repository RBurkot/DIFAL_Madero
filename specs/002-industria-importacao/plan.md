# Implementation Plan: Geração Automática da Planilha INDUSTRIA-IMPORTAÇÃO

**Branch**: `002-industria-importacao` | **Date**: 2026-06-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-industria-importacao/spec.md`

## Summary

Transformar automaticamente a aba de apuração `DIFAL MM.AAAA` em uma aba
`INDUSTRIA-IMPORTAÇÃO` pronta para importação contábil no ERP, replicando layout,
regras de débito/crédito, chaves de rastreio e totais consolidados da planilha
de referência `Cálculo DIFAL Industria até dia 28.xlsx`.

Abordagem técnica: **CLI Python** com `openpyxl`, pipeline em três etapas —
(1) leitura/validação da aba DIFAL, (2) enriquecimento opcional via abas
auxiliares (`SFT`, `BI QLVIEW`) para nome do fornecedor e datas, (3) geração da
aba de importação e relatório de reconciliação.

## Technical Context

**Language/Version**: Python 3.11+ (ambiente local 3.14 compatível)

**Primary Dependencies**: `openpyxl` (leitura/escrita Excel), `typer` (CLI),
`pydantic` (validação de modelos), `pytest` (testes)

**Storage**: Arquivos `.xlsx` no filesystem (entrada/saída); configuração em
`config/importacao.yaml` (limiar materialidade, contas fixas)

**Testing**: `pytest` com fixtures da planilha de referência 05/2026; testes de
contrato por chave e testes de integração ponta a ponta

**Target Platform**: Windows 10+ (PowerShell); execução local/offline

**Project Type**: CLI desktop (ferramenta de transformação de planilhas)

**Performance Goals**: Processar 350+ linhas DIFAL e gerar 200 lançamentos em
< 30 segundos em máquina corporativa típica

**Constraints**: Offline; sem expor dados fiscais em logs verbosos; layout de
saída fiel à referência; tolerância R$ 0,01/linha na reconciliação

**Scale/Scope**: 1 filial (`01GDIN0004`), 1 período por execução, ~350 linhas
entrada / ~200 lançamentos saída

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Gate | Status |
|-----------|------|--------|
| I. Precisão Fiscal | Regras de mapeamento débito/crédito e materialidade explícitas e validadas vs. referência? | [x] |
| II. Planilha como Entregável | Layout `INDUSTRIA-IMPORTAÇÃO` segue `Cálculo DIFAL Industria até dia 28.xlsx`? | [x] |
| III. Rastreabilidade | Chave, relatório de reconciliação e vínculo linha DIFAL → lançamento? | [x] |
| IV. Validação contra Referência | Baseline 05/2026 com 196 chaves e totais consolidados? | [x] |
| V. Simplicidade | CLI Python monolítico modular; sem ERP/API nesta feature? | [x] |

**Resultado**: [x] Aprovado para Phase 0  /  [ ] Bloqueado — violações em Complexity Tracking

**Nota pós-design**: Esta feature não recalcula DIFAL (dependência da feature 001);
garante precisão fiscal via transformação determinística e reconciliação contra
baseline. Princípio I atendido no escopo de lançamentos contábeis.

## Project Structure

### Documentation (this feature)

```text
specs/002-industria-importacao/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── workbook-io.md
│   └── reconciliation-report.md
└── tasks.md             # /speckit-tasks (não criado por /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── difal_importacao/
│   ├── __init__.py
│   ├── cli.py                 # Typer CLI: gerar-importacao
│   ├── config.py              # Carrega config/importacao.yaml
│   ├── models.py              # Pydantic: LinhaDifal, Lancamento, Totais
│   ├── reader.py              # Lê aba DIFAL + abas auxiliares
│   ├── transformer.py         # Regras débito/crédito, chave, filtro
│   ├── writer.py              # Escreve aba INDUSTRIA-IMPORTAÇÃO
│   └── reconciliation.py      # Compara com referência / emite relatório
├── config/
│   └── importacao.yaml        # Contas fixas, limiar, filial
tests/
├── fixtures/                  # Subconjunto anonimizado ou referência local
├── contract/
│   └── test_workbook_io.py
├── integration/
│   └── test_gerar_importacao_052026.py
└── unit/
    ├── test_transformer.py
    └── test_chave.py

pyproject.toml
README.md
```

**Structure Decision**: Projeto único com pacote `difal_importacao` e CLI.
Sem backend/frontend. Testes separados por unidade, contrato (schema de colunas)
e integração (baseline 05/2026).

## Complexity Tracking

> Nenhuma violação de constituição. Seção vazia.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
