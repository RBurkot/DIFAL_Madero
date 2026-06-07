---
description: "Task list for feature 002-industria-importacao"
---

# Tasks: Geração Automática da Planilha INDUSTRIA-IMPORTAÇÃO

**Input**: Design documents from `specs/002-industria-importacao/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Não solicitados explicitamente na spec; validação via reconciliação e testes manuais no quickstart (tarefas de verificação na fase Polish).

**Organization**: Tarefas agrupadas por user story para implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos distintos, sem dependências pendentes)
- **[Story]**: US1, US2, US3 conforme spec.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar projeto Python, estrutura de pacotes e configuração base

- [ ] T001 Criar estrutura de diretórios `src/difal_importacao/`, `config/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `tests/fixtures/` conforme plan.md
- [ ] T002 Criar `pyproject.toml` com dependências openpyxl, typer, pydantic e entry-point `difal-importacao` em `src/difal_importacao/cli.py`
- [ ] T003 [P] Criar `src/difal_importacao/__init__.py` com versão do pacote
- [ ] T004 [P] Criar `config/importacao.yaml` com limiar_materialidade, conta_icms_recolher, centro_custo, filial e tolerâncias conforme data-model.md
- [ ] T005 [P] Criar `README.md` na raiz com visão geral do CLI e link para `specs/002-industria-importacao/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Modelos, configuração e leitura da aba DIFAL — bloqueia todas as user stories

**⚠️ CRITICAL**: Nenhuma user story pode começar antes desta fase

- [ ] T006 Implementar `src/difal_importacao/config.py` para carregar e validar `config/importacao.yaml` com Pydantic
- [ ] T007 Implementar modelos Pydantic em `src/difal_importacao/models.py`: `PeriodoApuracao`, `LinhaApuracaoDifal`, `LancamentoImportacao`, `TotaisConsolidados`, `RelatorioReconciliacao`
- [ ] T008 Implementar detecção de aba DIFAL por regex `^DIFAL\s+\d{2}\.\d{4}\s*$` e extração de período em `src/difal_importacao/reader.py`
- [ ] T009 Implementar leitura de colunas obrigatórias da aba DIFAL em `src/difal_importacao/reader.py` conforme `contracts/workbook-io.md`
- [ ] T010 Implementar validação de layout (colunas ausentes, linhas vazias) com exceções descritivas em `src/difal_importacao/reader.py`
- [ ] T011 [P] Implementar função `build_chave_rastreio(nota, fornecedor, produto)` em `src/difal_importacao/transformer.py`
- [ ] T012 [P] Implementar validação `conta_contabil` (rejeitar `#N/A`, vazio, não numérico) em `src/difal_importacao/transformer.py`

**Checkpoint**: Leitura DIFAL funcional; modelos e config prontos

---

## Phase 3: User Story 1 - Gerar lançamentos a partir da apuração DIFAL (Priority: P1) 🎯 MVP

**Goal**: Transformar linhas DIFAL em lançamentos contábeis com débito/crédito corretos e aba `INDUSTRIA-IMPORTAÇÃO` gerada

**Independent Test**: Processar `DIFAL 05.2026` da referência; verificar lançamentos com colunas corretas; nota 13 com débito=conta e crédito=20140010007; nota 190054 com inversão para ajuste negativo

### Implementation for User Story 1

- [ ] T013 [US1] Implementar regra débito/crédito por sinal do ajuste (positivo/negativo) em `src/difal_importacao/transformer.py`
- [ ] T014 [US1] Implementar `transform_linha_difal(linha, config) -> LancamentoImportacao | None` em `src/difal_importacao/transformer.py`
- [ ] T015 [US1] Implementar escrita da aba `INDUSTRIA-IMPORTAÇÃO` (cabeçalho linha 4, colunas A–AA) em `src/difal_importacao/writer.py` conforme `contracts/workbook-io.md`
- [ ] T016 [US1] Implementar pipeline `gerar_lancamentos(linhas, periodo, config)` orquestrando transform em `src/difal_importacao/transformer.py`
- [ ] T017 [US1] Implementar subcomando `gerar` em `src/difal_importacao/cli.py` conforme `contracts/cli.md` (args, exit codes, stdout)
- [ ] T018 [US1] Integrar reader → transformer → writer no fluxo CLI em `src/difal_importacao/cli.py`
- [ ] T019 [US1] Validar manualmente amostra nota 13 e nota 190054 contra referência usando quickstart.md

**Checkpoint**: MVP funcional — CLI gera aba INDUSTRIA-IMPORTAÇÃO com lançamentos básicos

---

## Phase 4: User Story 2 - Filtrar elegíveis e consolidar totais (Priority: P2)

**Goal**: Excluir microajustes e exibir linha de totais consolidados no topo da aba

**Independent Test**: Processar DIFAL 05/2026 completo; confirmar ~196 lançamentos (não 336); totais linha 2 dentro de R$ 1,00 da referência

### Implementation for User Story 2

- [ ] T020 [US2] Implementar filtro de materialidade `abs(ajuste) >= limiar` em `src/difal_importacao/transformer.py`
- [ ] T021 [US2] Implementar contagem de linhas excluídas por materialidade para relatório em `src/difal_importacao/transformer.py`
- [ ] T022 [US2] Implementar agregação `TotaisConsolidados` sobre linhas DIFAL com ajuste ≠ 0 em `src/difal_importacao/transformer.py`
- [ ] T023 [US2] Implementar escrita da linha 2 (totais em colunas G–J) em `src/difal_importacao/writer.py`
- [ ] T024 [US2] Expor contagens (elegíveis, excluídas, geradas) no stdout/JSON do CLI em `src/difal_importacao/cli.py`

**Checkpoint**: Planilha com totais e filtro de materialidade alinhados à referência

---

## Phase 5: User Story 3 - Chave, histórico e vínculos auxiliares (Priority: P3)

**Goal**: Enriquecer lançamentos com dados SFT, chave, histórico, justificativa e tratamento de exceções

**Independent Test**: Validar 10 chaves contra referência; histórico truncado 28 chars; justificativa `AJUSTE FISCAL DIFAL 05.2026`; linhas `#N/A` sinalizadas sem lançamento incompleto

### Implementation for User Story 3

- [ ] T025 [US3] Implementar leitura da aba auxiliar `SFT` (ou `BI QLVIEW`) e índice por chave em `src/difal_importacao/reader.py`
- [ ] T026 [US3] Implementar enriquecimento `FornecedorLookup` (nome, loja, datas) em `src/difal_importacao/transformer.py`
- [ ] T027 [US3] Implementar composição de histórico `{nota}-{nome}` truncado a 28 chars em `src/difal_importacao/transformer.py`
- [ ] T028 [US3] Implementar justificativa `AJUSTE FISCAL DIFAL {MM.AAAA}` e código `F{cod}{loja}` em `src/difal_importacao/transformer.py`
- [ ] T029 [US3] Implementar flag `pendente_enriquecimento` e fallback de histórico com código fornecedor em `src/difal_importacao/transformer.py`
- [ ] T030 [US3] Adicionar opções `--aba-auxiliar` e `--sem-enriquecimento` ao CLI em `src/difal_importacao/cli.py`

**Checkpoint**: Lançamentos completos com rastreabilidade e metadados ERP

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Reconciliação, validação contra baseline e documentação final

- [ ] T031 Implementar `src/difal_importacao/reconciliation.py` comparando saída vs. referência por chave conforme `contracts/reconciliation-report.md`
- [ ] T032 Adicionar opções `--reconciliar` e `--relatorio` ao CLI em `src/difal_importacao/cli.py`
- [ ] T033 [P] Executar reconciliação completa período 05/2026 (196 chaves) e registrar resultado em `tests/fixtures/reconciliacao-052026.json`
- [ ] T034 [P] Validar fluxo ponta a ponta descrito em `specs/002-industria-importacao/quickstart.md`
- [ ] T035 Revisar logs do CLI para não expor valores fiscais completos em modo verbose em `src/difal_importacao/cli.py`
- [ ] T036 Atualizar `README.md` com exemplos PowerShell e critérios de aceite

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — iniciar imediatamente
- **Foundational (Phase 2)**: Depende de Setup — **BLOQUEIA** todas as user stories
- **US1 (Phase 3)**: Depende de Foundational — MVP
- **US2 (Phase 4)**: Depende de US1 (writer e transformer base)
- **US3 (Phase 5)**: Depende de US1; pode paralelizar parcialmente com US2 após T015
- **Polish (Phase 6)**: Depende de US1 + US2 + US3

### User Story Dependencies

```text
Foundational → US1 (P1) → US2 (P2) → US3 (P3) → Polish
                 ↓
               MVP entregável após US1
```

- **US1 (P1)**: Independente após Foundational — entrega CLI e lançamentos
- **US2 (P2)**: Estende transformer/writer de US1
- **US3 (P3)**: Estende reader/transformer de US1; independe de US2 para teste de chave/histórico

### Within Each User Story

- Modelos/config antes de transformer
- Transformer antes de writer
- Writer antes de CLI integration
- Story completa antes do checkpoint

### Parallel Opportunities

- **Phase 1**: T003, T004, T005 em paralelo após T001
- **Phase 2**: T011 e T012 em paralelo após T009
- **Phase 6**: T033 e T034 em paralelo
- **US2 e US3**: Após US1 completo, equipes distintas podem trabalhar US2 (totais) e US3 (enriquecimento) em paralelo com coordenação em `transformer.py`

---

## Parallel Example: User Story 1

```bash
# Sequencial obrigatório:
T013 → T014 → T015 → T016 → T017 → T018

# Após T015, em paralelo com polish futuro:
T011, T012 (foundational) já concluídos alimentam T013–T014
```

## Parallel Example: Pós-MVP

```bash
# Developer A — US2:
T020, T021, T022 → T023 → T024

# Developer B — US3:
T025 → T026, T027, T028, T029 → T030
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Phase 1: Setup
2. Completar Phase 2: Foundational (**CRITICAL**)
3. Completar Phase 3: User Story 1
4. **STOP and VALIDATE**: Quickstart com notas 13 e 190054
5. Demo para time contábil com aba gerada

### Incremental Delivery

1. Setup + Foundational → base pronta
2. US1 → lançamentos débito/crédito → **MVP**
3. US2 → filtro + totais → conferência fiscal
4. US3 → enriquecimento + chaves → pronto para ERP
5. Polish → reconciliação 196 chaves → entrega final

### Suggested MVP Scope

**User Story 1 apenas** (T001–T019): CLI gera `INDUSTRIA-IMPORTAÇÃO` com lançamentos
corretos para ajuste positivo/negativo, sem enriquecimento SFT e sem reconciliação
automatizada. Suficiente para demonstrar valor; US2/US3 refinam qualidade operacional.

---

## Task Summary

| Phase | Tasks | Story |
|-------|-------|-------|
| 1 Setup | T001–T005 (5) | — |
| 2 Foundational | T006–T012 (7) | — |
| 3 US1 P1 | T013–T019 (7) | US1 |
| 4 US2 P2 | T020–T024 (5) | US2 |
| 5 US3 P3 | T025–T030 (6) | US3 |
| 6 Polish | T031–T036 (6) | — |
| **Total** | **36** | |

### Independent Test Criteria

| Story | Criteria |
|-------|----------|
| US1 | Aba gerada; nota 13 débito/crédito correto; nota 190054 inversão |
| US2 | ~196 lançamentos; microajustes excluídos; totais linha 2 ±R$ 1,00 |
| US3 | 10 chaves corretas; histórico 28 chars; justificativa MM.AAAA |

### Format Validation

- [x] Todas as 36 tarefas usam `- [ ]`
- [x] Todas têm ID sequencial T001–T036
- [x] Tarefas paralelizáveis marcadas com [P]
- [x] Tarefas de user story marcadas com [US1], [US2] ou [US3]
- [x] Todas incluem caminho de arquivo explícito
