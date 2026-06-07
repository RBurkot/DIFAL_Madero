# Feature Specification: Geração Automática da Planilha DIFAL Indústria

**Feature Branch**: `001-auto-difal-industria`

**Created**: 2026-06-07

**Status**: Draft

**Input**: User description: "Geração automática da planilha DIFAL Indústria com base nos arquivos de referência existentes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar apuração DIFAL a partir do extrato BI (Priority: P1)

O analista fiscal da operação Indústria Madero (filial Ponta Grossa) precisa
gerar mensalmente a planilha de apuração DIFAL a partir do extrato de entradas
fiscais exportado do BI, sem recalcular manualmente linha a linha.

**Why this priority**: É o núcleo do valor de negócio — sem a apuração
calculada, não há base para conferência fiscal nem para lançamentos contábeis.
Corresponde à aba principal de cálculo (`DIFAL MM.AAAA`) da planilha de
referência `Cálculo DIFAL Industria até dia 28.xlsx`.

**Independent Test**: Informar um extrato BI de um mês com ao menos 10 notas de
diferentes UFs de origem e verificar que a planilha gerada contém, para cada
item, valor contábil, alíquotas, ICMS complementar, novo DIFAL e ajuste
coerentes com a planilha de referência para o mesmo período.

**Acceptance Scenarios**:

1. **Given** um arquivo de entrada no layout de `DIFAL INDUSTRIA BI.xlsx` com
   operações interestaduais para a filial `01GDIN0004` (PR), **When** o usuário
   solicita a geração da planilha DIFAL para o mês de apuração, **Then** o
   sistema produz uma planilha com colunas equivalentes à aba de cálculo da
   referência (fornecedor, UF origem, nota, produto, NCM, CFOP, valores,
   alíquotas, ICMS complementar, novo DIFAL e ajuste).

2. **Given** uma nota de fornecedor de SP com CFOP `2556` e valor contábil
   conhecido, **When** a apuração é gerada, **Then** o novo DIFAL e o ajuste
   para essa linha divergem no máximo R$ 0,01 em relação ao valor calculado na
   planilha de referência para o mesmo caso.

3. **Given** um período com corte em dia específico do mês (ex.: entradas até
   dia 28), **When** o usuário define o período de apuração, **Then** apenas
   notas com data de entrada dentro do intervalo informado entram no cálculo.

---

### User Story 2 - Gerar lançamentos contábeis de ajuste DIFAL (Priority: P2)

O analista fiscal precisa obter automaticamente os lançamentos contábeis de
ajuste fiscal DIFAL (débito/crédito, centros de custo, histórico) a partir dos
resultados da apuração, no mesmo formato da aba `INDUSTRIA-IMPORTAÇÃO` da
planilha de referência.

**Why this priority**: Após a apuração, o time contábil consome diretamente os
lançamentos; automatizar essa etapa elimina retrabalho e reduz erro de digitação
nas contas e valores de ajuste.

**Independent Test**: Gerar apuração para um subconjunto de notas com ajuste
diferente de zero e validar que a aba de lançamentos contém uma linha por
ajuste relevante, com débito, crédito, valor e histórico no padrão
`AJUSTE FISCAL DIFAL MM.AAAA`.

**Acceptance Scenarios**:

1. **Given** uma apuração com linhas cujo ajuste fiscal é diferente de zero,
   **When** a planilha completa é gerada, **Then** a aba de lançamentos contábeis
   lista cada ajuste com conta débito, conta crédito, valor do ajuste, chave de
   rastreio (nota + produto), datas de emissão e contabilização.

2. **Given** uma linha com ajuste inferior a R$ 0,01 em valor absoluto,
   **When** a planilha de lançamentos é gerada, **Then** essa linha é excluída
   ou agrupada conforme regra definida na referência (ajustes insignificantes
   não geram lançamento isolado).

---

### User Story 3 - Aplicar regras especiais por NCM e exceções fiscais (Priority: P3)

O analista fiscal precisa que regras tributárias específicas por NCM (como
redução de carga efetiva para determinados códigos) sejam aplicadas
automaticamente durante o cálculo, conforme tabela auxiliar da planilha de
referência.

**Why this priority**: Sem essas exceções, totais consolidados divergem da
apuração manual e comprometem a confiabilidade fiscal do processo.

**Independent Test**: Incluir no extrato de teste ao menos um NCM com regra
especial (ex.: `85437099` com carga efetiva de 8,80% em operações interestaduais
para Sul/Sudeste exceto ES) e validar que o DIFAL calculado reflete a regra.

**Acceptance Scenarios**:

1. **Given** uma operação interestadual com NCM cadastrado na tabela de exceções,
   **When** a apuração é gerada, **Then** a base de cálculo ou carga efetiva
   aplicada segue a regra documentada para aquele NCM.

2. **Given** um NCM sem regra especial cadastrada, **When** a apuração é gerada,
   **Then** o cálculo utiliza a regra padrão de diferencial de alíquotas
   (alíquota interna PR 19,5% menos alíquota interestadual conforme UF origem).

---

### Edge Cases

- Notas com conta contábil ausente (`#N/A`) na referência: o sistema MUST
  sinalizar a linha para revisão manual sem interromper o processamento das
  demais.
- CFOPs fora do escopo DIFAL (ex.: `2551` ativo imobilizado vs `2556` uso e
  consumo): o sistema MUST aplicar a regra correspondente ao tipo de operação
  conforme TES/descrição fiscal do extrato.
- Fornecedores de UFs com alíquota interestadual reduzida (4% ou 7%): o
  diferencial MUST refletir a combinação correta com a alíquota interna de PR.
- Extrato BI vazio ou sem notas no período: o sistema MUST informar que não há
  dados para apuração e entregar planilha estruturada sem linhas de cálculo.
- Duplicidade de chave nota + produto no extrato: o sistema MUST alertar e
  manter rastreabilidade sem somar valores indevidamente.
- Arquivo de entrada com layout divergente do padrão BI: o sistema MUST rejeitar
  com mensagem indicando colunas obrigatórias ausentes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar como entrada um arquivo tabular no layout
  equivalente a `DIFAL INDUSTRIA BI.xlsx` (colunas: período de entrada,
  fornecedor, UF origem, filial, nota fiscal, produto, NCM, CFOP, valores
  contábeis, alíquotas ICMS e ICMS complementar).

- **FR-002**: O sistema MUST permitir definir o período de apuração (mês/ano e,
  opcionalmente, data de corte no mês) para filtrar as notas incluídas.

- **FR-003**: O sistema MUST calcular, para cada linha elegível, alíquota
  complementar, valor ICMS complementar, novo DIFAL e ajuste (diferença entre
  novo DIFAL e ICMS complementar já destacado), usando alíquota interna de PR
  (19,5%) e alíquota interestadual conforme UF de origem do fornecedor.

- **FR-004**: O sistema MUST gerar planilha de saída em formato Excel (`.xlsx`)
  com aba de apuração detalhada estruturalmente equivalente à aba `DIFAL
  MM.AAAA` de `Cálculo DIFAL Industria até dia 28.xlsx`.

- **FR-005**: O sistema MUST gerar aba de lançamentos contábeis equivalente à
  aba `INDUSTRIA-IMPORTAÇÃO`, contendo débito, crédito, centro de custo, valor
  do ajuste, histórico padronizado e datas de emissão/contabilização.

- **FR-006**: O sistema MUST manter tabela parametrizável de regras especiais
  por NCM (equivalente à aba `Planilha1` da referência), aplicável durante o
  cálculo.

- **FR-007**: O sistema MUST produzir relatório ou aba de reconciliação que
  permita comparar totais gerados vs. planilha de referência (soma de novo
  DIFAL, soma de ajustes, quantidade de linhas).

- **FR-008**: O sistema MUST registrar, para cada valor calculado, os insumos
  utilizados (valor contábil, alíquota ICMS, alíquota complementar, UF origem,
  NCM, CFOP) de forma consultável na planilha ou em aba de auditoria.

- **FR-009**: O sistema MUST validar colunas obrigatórias na importação e
  rejeitar arquivos com layout incompatível antes de iniciar cálculos.

- **FR-010**: O sistema MUST restringir o escopo da v1 à operação Indústria da
  filial `01GDIN0004` (GD-P-IN-INDUSTRIA PONTA GROSSA - MATRIZ), conforme dados
  das planilhas de referência.

### Key Entities

- **Extrato BI de Entradas**: Conjunto de notas fiscais de entrada com dados de
  fornecedor, produto, valores, alíquotas e classificação fiscal; origem do
  processamento.

- **Linha de Apuração DIFAL**: Unidade de cálculo por nota/produto, com bases,
  alíquotas aplicadas, ICMS complementar, novo DIFAL e ajuste.

- **Regra Especial NCM**: Parametrização de tratamento fiscal diferenciado por
  código NCM (ex.: redução de carga efetiva), com vigência e descrição da regra.

- **Lançamento Contábil de Ajuste**: Registro de débito/crédito derivado de um
  ajuste DIFAL, vinculado a nota, fornecedor, contas contábeis e período.

- **Período de Apuração**: Mês/ano e critério de corte (ex.: entradas até dia
  28) que delimita o universo de notas processadas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O analista fiscal gera a planilha completa de um mês típico (500+
  linhas) em menos de 5 minutos, incluindo validação e exportação, versus o
  processo manual atual que exige horas de trabalho em planilha.

- **SC-002**: 100% das linhas de um extrato de teste representativo (amostra de
  pelo menos 50 notas do período 05/2026 presentes nas referências) apresentam
  novo DIFAL e ajuste com divergência máxima de R$ 0,01 por linha em relação à
  planilha `Cálculo DIFAL Industria até dia 28.xlsx`.

- **SC-003**: 100% dos lançamentos contábeis com ajuste acima de R$ 0,01 na
  amostra de teste possuem débito, crédito, valor e histórico coerentes com a
  aba `INDUSTRIA-IMPORTAÇÃO` da referência.

- **SC-004**: O tempo de conferência fiscal do período reduz em pelo menos 70%
  (medido pela eliminação do recálculo manual linha a linha, mantendo apenas
  revisão de exceções sinalizadas).

- **SC-005**: Zero regressões em totais consolidados (soma de ajustes do
  período) após qualquer alteração em regras parametrizadas, desde que validadas
  contra a baseline de referência antes da entrega.

## Assumptions

- A entrada da v1 será um arquivo exportado manualmente do BI/ERP no formato de
  `DIFAL INDUSTRIA BI.xlsx`; integração automática com ERP fica fora de escopo
  nesta versão.

- O período inicial de validação é **05/2026**, presente nas planilhas de
  referência do repositório; novos períodos seguem as mesmas regras.

- A filial alvo é exclusivamente `01GDIN0004` (Indústria Ponta Grossa/PR); demais
  filiais ou operações (varejo, CD) ficam fora de escopo.

- Alíquota interna de destino é **19,5%** (PR); alíquotas interestaduais seguem
  tabela padrão por UF de origem (4%, 7% ou 12% conforme convênio e tipo de
  operação indicado no extrato).

- Arredondamento monetário adota **2 casas decimais** em valores finais (novo
  DIFAL, ajuste, lançamentos), tolerando micro-diferenças de arredondamento até
  R$ 0,01 por linha.

- Contas contábeis de débito/crédito seguem mapeamento existente na referência;
  exceções de conta (aba `AJUSTES`) serão tratadas na fase de planejamento com
  base nas regras documentadas na planilha de referência.

- O usuário primário é o analista fiscal/contábil interno Madero com
  conhecimento das planilhas atuais; não há portal self-service para terceiros
  nesta versão.

## Fiscal Compliance *(mandatory for DIFAL features)*

### Regras de Cálculo

- **Período de apuração**: Mensal, com filtro por `MES_ANO_ENTRADA` e opção de
  corte por data de entrada (ex.: até dia 28 do mês), conforme nome e conteúdo
  da planilha `Cálculo DIFAL Industria até dia 28.xlsx`.

- **UFs envolvidas**: UF de origem conforme fornecedor no extrato BI; UF de
  destino fixa **PR** (filial industria Ponta Grossa).

- **Bases e alíquotas**: Valor contábil como base; alíquota ICMS destacada na
  nota; alíquota complementar = alíquota interna PR (19,5%) − alíquota
  interestadual aplicável; novo DIFAL = valor contábil × alíquota complementar
  (com ajustes por regra especial NCM quando aplicável); ajuste = novo DIFAL −
  valor ICMS complementar já informado no extrato.

- **Arredondamento**: Valores monetários com 2 casas decimais; tolerância de
  reconciliação de R$ 0,01 por linha.

### Validação e Referência

- **Planilha de referência primária**: `Cálculo DIFAL Industria até dia 28.xlsx`
  (apuração, lançamentos, regras NCM, ajustes).

- **Planilha de referência de entrada**: `DIFAL INDUSTRIA BI.xlsx` (layout e
  conteúdo do extrato BI).

- **Critério de aceite numérico**: Divergência máxima de **R$ 0,01 por linha** em
  novo DIFAL e ajuste; totais consolidados de ajuste idênticos à referência
  para o período de teste 05/2026.

- **Cenários fiscais de borda**: Operações de SP/SC/RJ/ES/BA com alíquotas
  distintas; CFOP `2551` (ativo) vs `2556` (uso/consumo); NCM com regra especial
  (`85437099`); notas com ICMS retido; linhas com conta contábil ausente;
  ajustes próximos de zero; período sem movimentação.
