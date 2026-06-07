# Feature Specification: Frontend de Seleção de Arquivos e Acompanhamento de Processamento

**Feature Branch**: `003-difal-frontend`

**Created**: 2026-06-07

**Status**: Draft

**Input**: User description: "Front end, para seleção dos arquivos, acompanhamento do processamento."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Selecionar arquivos e iniciar processamento DIFAL (Priority: P1)

O analista fiscal/contábil da Indústria Madero precisa de uma interface gráfica
para escolher os arquivos de entrada do fluxo DIFAL (extrato BI e/ou planilha
com aba DIFAL já apurada), informar o período de apuração e iniciar o
processamento sem usar linha de comando.

**Why this priority**: Sem seleção de arquivos e disparo do fluxo, o usuário
de negócio não consegue operar as features 001 e 002 de forma autônoma; é o
ponto de entrada obrigatório da solução.

**Independent Test**: Abrir a interface, selecionar arquivo BI válido e período
05/2026, iniciar processamento e verificar que o sistema aceita os arquivos,
valida o layout e confirma o início da execução com mensagem clara.

**Acceptance Scenarios**:

1. **Given** a tela inicial do sistema, **When** o usuário seleciona um arquivo
   `.xlsx` de extrato BI no layout `DIFAL INDUSTRIA BI.xlsx`, **Then** o sistema
   exibe nome do arquivo, tamanho e status de validação (válido ou erro de
   layout).

2. **Given** arquivos de entrada válidos e período `05/2026` informado,
   **When** o usuário clica em iniciar processamento, **Then** o sistema
   registra a solicitação e apresenta estado "em processamento" com identificador
   da execução visível na tela.

3. **Given** um arquivo com extensão ou layout inválido, **When** o usuário
   tenta iniciar o processamento, **Then** o sistema bloqueia o início e exibe
   mensagem indicando o problema (ex.: colunas obrigatórias ausentes), sem
   processar dados parcialmente.

---

### User Story 2 - Acompanhar etapas e progresso do processamento (Priority: P2)

O analista fiscal precisa visualizar em tempo real (ou quase real) em qual etapa
o processamento está, quanto já foi concluído e se houve avisos ou erros, para
saber quando a planilha estará pronta e se deve intervir.

**Why this priority**: Processamentos mensais podem levar minutos e envolvem
múltiplas etapas (apuração DIFAL, geração INDUSTRIA-IMPORTAÇÃO, reconciliação);
sem acompanhamento, o usuário não tem confiança nem previsibilidade.

**Independent Test**: Iniciar processamento de um período típico e verificar que
a interface atualiza etapas sequenciais (validação → apuração → importação →
reconciliação) com percentual ou contadores até conclusão ou falha.

**Acceptance Scenarios**:

1. **Given** um processamento em andamento, **When** cada etapa do pipeline é
   concluída, **Then** a interface atualiza indicador visual da etapa atual e
   das etapas já finalizadas (ex.: "Apuração DIFAL", "INDUSTRIA-IMPORTAÇÃO",
   "Reconciliação").

2. **Given** um processamento em andamento, **When** a etapa de apuração processa
   as linhas do extrato, **Then** o usuário vê contadores de progresso (linhas
   processadas, lançamentos gerados ou equivalente em linguagem de negócio).

3. **Given** uma falha em etapa intermediária, **When** o processamento é
   interrompido, **Then** a interface exibe etapa que falhou, motivo resumido e
   orientação de correção (ex.: "conta contábil inválida na linha X"), sem
   expor dados fiscais sensíveis completos na mensagem.

---

### User Story 3 - Consultar resultado e baixar planilhas geradas (Priority: P3)

O analista fiscal/contábil precisa, ao final do processamento, visualizar um
resumo do resultado (totais, reconciliação, alertas) e baixar as planilhas
geradas (apuração DIFAL e INDUSTRIA-IMPORTAÇÃO) diretamente pela interface.

**Why this priority**: O valor final são as planilhas prontas e a confiança na
apuração; a interface deve fechar o ciclo entregando artefatos e evidências de
conformidade.

**Independent Test**: Concluir processamento de 05/2026 e verificar que a tela
de resultado exibe totais consolidados, status de reconciliação e permite
download dos arquivos de saída.

**Acceptance Scenarios**:

1. **Given** um processamento concluído com sucesso, **When** o usuário acessa a
   tela de resultado, **Then** o sistema exibe resumo com período, quantidade de
   linhas processadas, lançamentos gerados e status da reconciliação (aprovado
   ou reprovado).

2. **Given** um processamento concluído com sucesso, **When** o usuário solicita
   download, **Then** o sistema disponibiliza planilha(s) de saída em formato
   Excel com abas esperadas (`DIFAL MM.AAAA` e/ou `INDUSTRIA-IMPORTAÇÃO`).

3. **Given** um processamento concluído com ressalvas (ex.: linhas sinalizadas
   para revisão manual), **When** o usuário visualiza o resultado, **Then** o
   sistema lista alertas de forma resumida com opção de exportar relatório de
   exceções, sem bloquear download das planilhas já geradas quando aplicável.

---

### Edge Cases

- Usuário fecha a interface durante processamento: o sistema MUST manter estado
  recuperável na mesma sessão ou informar claramente que a execução continua em
  segundo plano.
- Dois processamentos simultâneos na mesma máquina: o sistema MUST impedir ou
  enfileirar explicitamente para evitar sobrescrita de arquivos de saída.
- Arquivo de entrada bloqueado (aberto no Excel): o sistema MUST informar erro de
  acesso e orientar fechar o arquivo.
- Período informado divergente do conteúdo do arquivo: o sistema MUST alertar
  antes de processar.
- Falha de reconciliação: o sistema MUST marcar resultado como reprovado e
  ainda permitir download para análise, com destaque visual do status.
- Ausência de conexão de rede: o sistema MUST operar integralmente em ambiente
  local (processamento offline), pois dados fiscais não dependem de nuvem nesta v1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST oferecer interface gráfica para seleção de arquivos
  de entrada (extrato BI `.xlsx` e/ou planilha com aba DIFAL apurada).

- **FR-002**: O sistema MUST permitir informar período de apuração (mês/ano) e,
  opcionalmente, data de corte no mês, antes de iniciar o processamento.

- **FR-003**: O sistema MUST validar arquivos selecionados (extensão, layout,
  colunas obrigatórias) e exibir feedback imediato antes da execução.

- **FR-004**: O sistema MUST permitir iniciar o pipeline completo (apuração DIFAL
  + geração INDUSTRIA-IMPORTAÇÃO) ou etapas individuais quando os arquivos de
  entrada já cobrem etapas anteriores.

- **FR-005**: O sistema MUST exibir acompanhamento do processamento com etapas
  nomeadas, estado (pendente, em andamento, concluído, erro) e indicadores de
  progresso compreensíveis para usuário de negócio.

- **FR-006**: O sistema MUST apresentar tela de resultado com resumo quantitativo
  (linhas, lançamentos, totais, status de reconciliação) ao término.

- **FR-007**: O sistema MUST permitir download das planilhas de saída geradas na
  execução, em formato Excel.

- **FR-008**: O sistema MUST registrar histórico das últimas execuções da sessão
  (data, período, arquivos, status) para consulta rápida pelo usuário.

- **FR-009**: O sistema MUST exibir alertas e exceções (conta inválida, linhas
  excluídas por materialidade, pendências de enriquecimento) em linguagem de
  negócio, com opção de exportar relatório resumido.

- **FR-010**: O sistema MUST operar em português e MUST NOT exibir valores
  fiscais completos de terceiros em mensagens de erro em tela pública/log visível
  ao usuário casual.

- **FR-011**: O sistema MUST restringir escopo à operação Indústria Madero
  (filial `01GDIN0004`) e aos fluxos definidos nas features 001 e 002.

### Key Entities

- **Sessão de Processamento**: Execução iniciada pelo usuário com identificador,
  período, arquivos de entrada, estado atual e horários de início/fim.

- **Arquivo de Entrada**: Referência ao arquivo selecionado (nome, tipo BI ou
  DIFAL, status de validação).

- **Etapa do Pipeline**: Fase do fluxo (validação, apuração DIFAL, geração
  INDUSTRIA-IMPORTAÇÃO, reconciliação) com status e métricas de progresso.

- **Resultado da Execução**: Resumo pós-processamento com totais, status de
  reconciliação, alertas e links para download.

- **Histórico de Execução**: Registro consultável das execuções recentes na
  sessão do usuário.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários de negócio iniciam um processamento completo (seleção de
  arquivos até disparo) em menos de 2 minutos, sem assistência técnica.

- **SC-002**: 100% das etapas do pipeline exibem atualização de status em até 5
  segundos após mudança de estado durante o processamento.

- **SC-003**: 90% dos usuários piloto concluem o fluxo completo (entrada →
  acompanhamento → download) na primeira tentativa, sem consultar documentação
  técnica.

- **SC-004**: Tempo entre conclusão do processamento e disponibilidade do
  download na interface é inferior a 10 segundos.

- **SC-005**: Redução de 80% nas solicitações de suporte relacionadas a "como
  rodar o processamento" em relação ao fluxo exclusivamente via linha de comando.

## Assumptions

- Usuários primários são analistas fiscal/contábil internos Madero, em ambiente
  corporativo Windows, com acesso aos arquivos `.xlsx` locais ou em pasta de
  rede.

- A interface é **local/desktop ou intranet** nesta v1; publicação em internet
  pública fica fora de escopo.

- O processamento fiscal em si é realizado pelos motores das features 001 e 002;
  esta feature é camada de interação e orquestração, sem alterar regras de cálculo.

- Autenticação corporativa (SSO/AD) não é obrigatória na v1; acesso restrito por
  ambiente de rede corporativa é suficiente inicialmente.

- Um processamento por vez por instância da aplicação na v1; fila de execuções é
  desejável mas não obrigatória no MVP.

- Idioma da interface: português (Brasil).

## Fiscal Compliance *(mandatory for DIFAL features)*

### Regras de Cálculo

- **Período de apuração**: Informado pelo usuário na interface e repassado ao
  pipeline; a UI MUST alertar divergências detectáveis entre período informado e
  metadados do arquivo.

- **UFs envolvidas / bases / alíquotas**: Não calculadas pela interface; exibidas
  apenas em resumos produzidos pelo motor de apuração (feature 001).

- **Arredondamento**: Política fiscal permanece nos motores de backend; a UI
  apresenta resultados já arredondados sem reprocessar valores.

### Validação e Referência

- **Planilhas de referência**: `DIFAL INDUSTRIA BI.xlsx`, `Cálculo DIFAL Industria
  até dia 28.xlsx` — usadas como baseline visual de layout e reconciliação.

- **Critério de aceite na interface**: Status de reconciliação exibido deve
  refletir o mesmo resultado do motor (aprovado/reprovado) com tolerâncias já
  definidas nas features 001/002 (R$ 0,01/linha).

- **Cenários fiscais de borda na UI**: Exibir claramente execuções com
  ressalvas (microajustes excluídos, contas inválidas, reconciliação reprovada)
  sem ocultar o status ao usuário.
