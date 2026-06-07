# Feature Specification: Geração Automática da Planilha INDUSTRIA-IMPORTAÇÃO

**Feature Branch**: `002-industria-importacao`

**Created**: 2026-06-07

**Status**: Draft

**Input**: User description: "Geração automática da planilha INDUSTRIA-IMPORTACAO com base na planilha gerada DIFAL MM.AAAA"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar lançamentos a partir da apuração DIFAL (Priority: P1)

O analista contábil da Indústria Madero precisa transformar automaticamente os
resultados da aba de apuração `DIFAL MM.AAAA` em uma planilha de lançamentos
contábeis no formato `INDUSTRIA-IMPORTAÇÃO`, sem montar manualmente cada linha
de débito, crédito e histórico.

**Why this priority**: É o entregável consumido diretamente pelo time contábil
para contabilização do ajuste fiscal DIFAL; sem esta etapa, a apuração calculada
não se converte em ação operacional.

**Independent Test**: Informar uma aba `DIFAL 05.2026` de referência com pelo
menos 20 linhas com ajuste material e verificar que a planilha
`INDUSTRIA-IMPORTAÇÃO` gerada contém lançamentos com colunas, totais e
justificativa coerentes com a aba homônima de `Cálculo DIFAL Industria até dia
28.xlsx`.

**Acceptance Scenarios**:

1. **Given** uma planilha com aba `DIFAL MM.AAAA` contendo linhas com ajuste
   fiscal calculado, **When** o usuário solicita a geração da planilha
   `INDUSTRIA-IMPORTAÇÃO` para o período, **Then** o sistema produz aba com
   cabeçalho e colunas equivalentes à referência (loja, nota, fornecedor,
   produto, CFOP, valores DIFAL, chave, datas, filial, débito, crédito, valor
   do lançamento, histórico e justificativa).

2. **Given** uma linha da apuração com ajuste positivo e conta contábil válida,
   **When** o lançamento é gerado, **Then** a conta contábil da linha DIFAL
   compõe o **débito**, a conta `20140010007` (ICMS a recolher) compõe o
   **crédito**, e o **valor** do lançamento corresponde ao ajuste positivo.

3. **Given** uma linha da apuração com ajuste negativo, **When** o lançamento é
   gerado, **Then** débito e crédito são invertidos em relação ao caso positivo
   e o valor do lançamento corresponde ao módulo do ajuste.

---

### User Story 2 - Filtrar linhas elegíveis e consolidar totais do período (Priority: P2)

O analista fiscal precisa que apenas linhas com ajuste fiscal relevante gerem
lançamento contábil, e que a planilha exiba totais consolidados do período no
topo da aba, como na referência manual.

**Why this priority**: Evita poluir a contabilização com microdiferenças de
arredondamento e fornece conferência rápida dos totais de valor de nota, DIFAL,
novo DIFAL e ajuste do período.

**Independent Test**: Processar aba DIFAL completa de 05/2026 e validar que o
número de lançamentos e os totais consolidados do cabeçalho correspondem à aba
`INDUSTRIA-IMPORTAÇÃO` da planilha de referência (tolerância R$ 0,01 nos
totais).

**Acceptance Scenarios**:

1. **Given** linhas da apuração cujo ajuste absoluto é inferior ao limiar de
   materialidade definido (padrão: R$ 0,01), **When** a planilha de importação
   é gerada, **Then** essas linhas são excluídas dos lançamentos contábeis.

2. **Given** um conjunto de lançamentos elegíveis para o período `MM.AAAA`,
   **When** a aba é gerada, **Then** uma linha de totais no topo consolida
   valor da nota, DIFAL (ICMS complementar), novo DIFAL e ajuste do período,
   coerente com a soma das linhas elegíveis.

---

### User Story 3 - Montar chave, histórico e vínculos contábeis auxiliares (Priority: P3)

O analista contábil precisa que cada lançamento traga identificadores e textos
padronizados para importação no ERP, incluindo chave única, histórico resumido
e códigos auxiliares de fornecedor e item contábil.

**Why this priority**: Garante rastreabilidade e compatibilidade com o processo
de importação contábil existente, reduzindo rejeições no ERP.

**Independent Test**: Validar amostra de 10 lançamentos gerados contra a
referência verificando chave, histórico truncado, código fornecedor (`F{cod}{loja}`)
e centro de custo `290001`.

**Acceptance Scenarios**:

1. **Given** uma linha DIFAL com nota `000149577`, fornecedor `200033` e produto
   `10724652001700`, **When** o lançamento é gerado, **Then** a chave de
   rastreio é `14957720003310724652001700` (nota sem zeros à esquerda +
   fornecedor + produto).

2. **Given** o período de apuração `05/2026`, **When** qualquer lançamento é
   gerado, **Then** a justificativa segue o padrão `AJUSTE FISCAL DIFAL 05.2026`
   e o histórico segue o padrão `{nota}-{nome fornecedor truncado}`.

3. **Given** uma linha com conta contábil ausente ou inválida na apuração DIFAL,
   **When** a geração é executada, **Then** a linha é sinalizada para revisão
   manual e não gera lançamento automático incompleto.

---

### Edge Cases

- Linha DIFAL com ajuste exatamente zero: MUST ser ignorada na geração de
  lançamentos.
- Linha DIFAL com ajuste negativo de grande magnitude: MUST inverter débito e
  crédito usando valor absoluto, conforme padrão da referência (ex.: nota 190054
  com produto distinto).
- Múltiplas linhas DIFAL para a mesma nota e produtos diferentes: MUST gerar um
  lançamento independente por linha de produto.
- Nome de fornecedor ausente na apuração: MUST compor histórico com código
  fornecedor e sinalizar para complementação manual.
- Aba DIFAL com nome de período divergente (ex.: `DIFAL 06.2026`): MUST extrair
  período do nome da aba para compor justificativa e metadados.
- Planilha de entrada sem aba DIFAL no padrão esperado: MUST rejeitar com
  mensagem indicando aba obrigatória ausente.
- Loja do fornecedor diferente de `0001`/`0002`: MUST preservar loja informada
  na apuração e refletir no código fornecedor (`F{cod}{loja}`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar como entrada uma planilha contendo aba de
  apuração no formato `DIFAL MM.AAAA` (saída da feature `001-auto-difal-industria`
  ou planilha equivalente validada).

- **FR-002**: O sistema MUST gerar aba `INDUSTRIA-IMPORTAÇÃO` em Excel (`.xlsx`)
  estruturalmente equivalente à aba homônima de `Cálculo DIFAL Industria até dia
  28.xlsx`.

- **FR-003**: O sistema MUST mapear campos da apuração DIFAL para colunas de
  importação: fornecedor → código/nome; nota fiscal → nota; código produto →
  produto; código fiscal → CFOP; valor contábil → valor da nota; valor ICMS
  complementar → DIFAL; novo DIFAL e ajuste → colunas homônimas.

- **FR-004**: O sistema MUST gerar lançamento contábil apenas para linhas cujo
  ajuste absoluto seja igual ou superior a R$ 0,01 (limiar de materialidade
  parametrizável).

- **FR-005**: Para ajuste positivo, o sistema MUST lançar **débito** na conta
  contábil da linha DIFAL e **crédito** na conta `20140010007`; para ajuste
  negativo, MUST inverter débito e crédito e usar valor absoluto do ajuste.

- **FR-006**: O sistema MUST compor chave de rastreio concatenando nota fiscal
  (sem zeros à esquerda), código fornecedor e código produto.

- **FR-007**: O sistema MUST preencher centro de custo `290001`, código
  fornecedor no formato `F{codigo_fornecedor}{loja}` e justificativa
  `AJUSTE FISCAL DIFAL MM.AAAA` extraída do período da aba DIFAL.

- **FR-008**: O sistema MUST gerar linha de totais consolidados no topo da aba
  (valor da nota, DIFAL, novo DIFAL e ajuste) para o conjunto de lançamentos
  elegíveis do período.

- **FR-009**: O sistema MUST preservar datas de emissão e entrada quando
  disponíveis na apuração ou em fonte complementar vinculada; quando ausentes,
  MUST sinalizar campo pendente sem bloquear demais lançamentos.

- **FR-010**: O sistema MUST produzir relatório de reconciliação indicando:
  total de linhas na apuração DIFAL, linhas elegíveis, lançamentos gerados,
  linhas excluídas por materialidade e linhas sinalizadas por conta inválida.

- **FR-011**: O sistema MUST restringir escopo à filial `01GDIN0004` e operação
  Indústria, coerente com as planilhas de referência do projeto.

### Key Entities

- **Linha de Apuração DIFAL**: Registro da aba `DIFAL MM.AAAA` com dados fiscais
  e contábeis de origem (fornecedor, nota, produto, CFOP, valores, conta
  contábil, novo DIFAL, ajuste).

- **Lançamento de Importação Contábil**: Registro derivado de uma linha DIFAL
  elegível, com débito, crédito, valor, chave, histórico, justificativa e datas.

- **Período de Apuração**: Mês/ano extraído do nome da aba DIFAL (ex.:
  `05.2026`), usado em justificativa e metadados.

- **Totais Consolidados**: Agregação de valores do período exibida no cabeçalho
  da aba `INDUSTRIA-IMPORTAÇÃO`.

- **Mapeamento de Contas**: Regra que define débito/crédito a partir do sinal do
  ajuste e da conta contábil da linha DIFAL.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O analista contábil gera a planilha `INDUSTRIA-IMPORTAÇÃO` de um
  período completo em menos de 2 minutos, incluindo validação, versus dezenas
  de minutos de montagem manual.

- **SC-002**: 100% dos lançamentos da amostra de teste 05/2026 (196 chaves
  presentes na referência) apresentam débito, crédito e valor com divergência
  máxima de R$ 0,01 em relação à aba `INDUSTRIA-IMPORTAÇÃO` de `Cálculo DIFAL
  Industria até dia 28.xlsx`.

- **SC-003**: Totais consolidados do cabeçalho (valor da nota, DIFAL, novo DIFAL
  e ajuste) divergem no máximo R$ 1,00 do total da referência para o período
  05/2026, considerando exclusão de microajustes.

- **SC-004**: 100% das chaves de rastreio geradas na amostra de teste coincidem
  com o padrão de composição validado na referência.

- **SC-005**: Zero lançamentos automáticos com conta débito ou crédito ausente;
  linhas problemáticas são sinalizadas em relatório de exceções em vez de
  exportadas incompletas.

## Assumptions

- A aba `DIFAL MM.AAAA` já existe e foi validada (feature `001-auto-difal-industria`
  ou planilha manual equivalente); esta feature não recalcula DIFAL.

- O período inicial de validação é **05/2026**, com baseline na aba
  `INDUSTRIA-IMPORTAÇÃO` de `Cálculo DIFAL Industria até dia 28.xlsx`.

- Loja padrão do fornecedor é `0001`; quando a apuração indicar outra loja
  (ex.: `0002`), o código `F{cod}{loja}` reflete a loja informada.

- Conta crédito/débito de contrapartida padrão para ajuste positivo é
  `20140010007` (ICMS a recolher), conforme referência.

- Centro de custo padrão é `290001` para todos os lançamentos da amostra de
  referência.

- Limiar de materialidade padrão para geração de lançamento é **R$ 0,01** de
  ajuste absoluto; microdiferenças abaixo disso são excluídas, coerente com o
  comportamento observado na referência (127 linhas com ajuste não importadas).

- Nome do fornecedor (`NOME FORNE`) pode exigir fonte complementar quando ausente
  na aba DIFAL; nestes casos, histórico usa identificador mínimo e sinalização.

- Código item contábil auxiliar segue padrão da referência quando disponível na
  apuração; ausências são permitidas com sinalização (conforme linhas com campo
  em branco na referência).

## Fiscal Compliance *(mandatory for DIFAL features)*

### Regras de Cálculo

- **Período de apuração**: Extraído do sufixo da aba de entrada `DIFAL MM.AAAA`
  (ex.: `DIFAL 05.2026`).

- **UFs envolvidas**: Não recalculadas nesta feature; valores de DIFAL, novo
  DIFAL e ajuste são consumidos como produzidos na aba de apuração.

- **Bases e alíquotas**: Não aplicáveis — esta feature transforma resultados já
  apurados em lançamentos contábeis.

- **Arredondamento**: Valor do lançamento com 2 casas decimais; tolerância de
  reconciliação de R$ 0,01 por lançamento.

### Validação e Referência

- **Planilha de referência primária**: aba `INDUSTRIA-IMPORTAÇÃO` de `Cálculo
  DIFAL Industria até dia 28.xlsx`.

- **Planilha de entrada esperada**: aba `DIFAL 05.2026` (ou equivalente
  `DIFAL MM.AAAA`) da mesma planilha de referência ou gerada pela feature 001.

- **Critério de aceite numérico**: Divergência máxima de **R$ 0,01 por
  lançamento** em valor, débito e crédito; totais consolidados com tolerância
  de **R$ 1,00** no período 05/2026.

- **Cenários fiscais de borda**: Ajuste positivo vs negativo (inversão
  débito/crédito); CFOP `2551` vs `2556` com contas de débito distintas;
  microajustes abaixo de R$ 0,01; conta contábil ausente; múltiplos produtos
  por nota; fornecedor com loja `0002`.
