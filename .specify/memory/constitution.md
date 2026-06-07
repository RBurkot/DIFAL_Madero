<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Modified principles: N/A (initial ratification)
- Added sections:
  - Core Principles (5)
  - Restrições Fiscais e de Dados
  - Fluxo de Desenvolvimento e Qualidade
  - Governance
- Removed sections: N/A
- Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/*.md ⚠ N/A (diretório inexistente)
  - README.md ⚠ pending (arquivo inexistente)
- Follow-up TODOs:
  - TODO(RATIFICATION_APPROVER): confirmar responsável pela ratificação formal
  - TODO(REFERENCE_SPREADSHEET_VERSION): versionar planilhas de referência em specs/
-->

# Geração Planilha DIFAL Constitution

## Core Principles

### I. Precisão Fiscal (NON-NEGOTIABLE)

Todo cálculo de DIFAL (Diferencial de Alíquotas) MUST refletir a legislação
vigente, convenções de ICMS interestadual e regras de negócio acordadas com o
cliente Madero. Fórmulas, bases de cálculo, alíquotas internas/interestaduais
e arredondamentos MUST ser explícitos, documentados e reproduzíveis. Divergência
em relação às planilhas de referência existentes no repositório MUST ser
investigada e resolvida antes de qualquer entrega.

**Rationale**: Erros fiscais geram passivo tributário, retrabalho e perda de
confiança. A precisão é o critério primário de aceite do projeto.

### II. Planilha como Entregável Primário

A saída principal do sistema MUST ser uma planilha (Excel ou formato
equivalente acordado) utilizável pelo time fiscal/contábil sem depender de
código-fonte. Layout, abas, colunas, totais e indicadores MUST seguir o padrão
das referências `DIFAL INDUSTRIA BI.xlsx` e `Cálculo DIFAL Industria até dia
28.xlsx`, salvo mudança formalmente especificada e aprovada.

**Rationale**: O valor de negócio é a planilha pronta para conferência,
apuração e integração com processos existentes.

### III. Rastreabilidade e Auditabilidade

Cada valor calculado MUST ser rastreável até sua origem: período de apuração,
UF de origem/destino, base de cálculo, alíquota aplicada e regra utilizada.
Transformações de dados (importação, agregação, filtros) MUST registrar origem e
critério aplicado. Logs ou artefatos de reconciliação MUST permitir explicar
qualquer divergência entre entrada, processamento e saída.

**Rationale**: Apurações fiscais exigem justificativa auditável em conferências
internas e eventuais questionamentos externos.

### IV. Validação contra Referência

Antes de considerar uma feature concluída, MUST existir validação comparativa
contra planilhas de referência ou conjunto de casos de teste fiscalmente
representativos. Cenários de borda (operações isentas, alíquotas reduzidas,
múltiplas UFs, períodos parciais, dados ausentes) MUST ser cobertos. Regressões
em valores já validados MUST bloquear entrega até correção.

**Rationale**: Planilhas legadas são a fonte de verdade operacional até que uma
nova baseline seja formalmente adotada.

### V. Simplicidade e Manutenibilidade

A solução MUST priorizar o caminho mais simples que atenda aos requisitos
fiscais: evitar abstrações desnecessárias, dependências excessivas ou lógica
duplicada entre código e planilha. Regras tributárias voláteis MUST ficar
centralizadas e parametrizadas (tabelas de alíquotas, UFs, vigências). Qualquer
complexidade adicional MUST ser justificada no plano de implementação.

**Rationale**: Regras de DIFAL e layouts de planilha evoluem; código simples
reduz custo de manutenção e risco de erro em alterações futuras.

## Restrições Fiscais e de Dados

- Escopo inicial: geração de planilha DIFAL para operação **Indústria** do
  cliente Madero, com apuração por período definido nas especificações.
- Dados de entrada MUST preservar integridade: CNPJ, UF, valores, CFOP/NCM ou
  demais campos exigidos pela spec da feature MUST ser validados na importação.
- Dados sensíveis (faturamento, bases de cálculo, identificadores fiscais) MUST
  NOT ser expostos em logs públicos, commits ou artefatos compartilhados sem
  necessidade.
- Alterações em regras tributárias MUST ser documentadas com vigência e impacto
  nos cálculos antes da implementação.
- Formato de saída padrão: Excel (`.xlsx`), compatível com versões corporativas
  em uso pelo cliente, salvo definição contrária na spec.

## Fluxo de Desenvolvimento e Qualidade

- Toda feature MUST seguir o fluxo Spec Kit: `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`.
- O **Constitution Check** no plano MUST validar conformidade com os cinco
  princípios antes de iniciar implementação.
- Specs MUST descrever cenários fiscais em linguagem de negócio, com critérios
  de aceite mensuráveis (ex.: divergência máxima permitida vs. referência).
- Tasks MUST incluir etapa de reconciliação/validação quando a feature alterar
  cálculos ou layout da planilha.
- Entregas MUST passar por revisão cruzada: regra fiscal + consistência de
  planilha + rastreabilidade dos dados.
- Mudanças que afetem totais consolidados MUST incluir evidência de teste
  (amostra de período, UF ou operação representativa).

## Governance

Esta constituição supersede práticas ad hoc e define os critérios não
negociáveis do projeto Geração Planilha DIFAL.

**Procedimento de emenda**

1. Propor alteração com justificativa de impacto fiscal, técnico e operacional.
2. Classificar bump de versão (MAJOR/MINOR/PATCH) conforme semântica abaixo.
3. Atualizar `.specify/memory/constitution.md` e sincronizar templates
   dependentes (`plan-template.md`, `spec-template.md`, `tasks-template.md`).
4. Registrar data de emenda e, se aplicável, nova baseline de planilha de
   referência.

**Política de versionamento da constituição**

- **MAJOR**: remoção ou redefinição incompatível de princípio fiscal central.
- **MINOR**: novo princípio, seção obrigatória ou expansão material de governança.
- **PATCH**: clarificações, correções textuais sem mudança de obrigação.

**Revisão de conformidade**

- Cada plano (`plan.md`) MUST incluir Constitution Check explícito.
- Violações MUST ser documentadas em Complexity Tracking com alternativa mais
  simples rejeitada e justificativa.
- Revisões periódicas MUST ocorrer quando houver mudança legislativa relevante
  ou troca de planilha de referência.

**Version**: 1.0.0 | **Ratified**: 2026-06-07 | **Last Amended**: 2026-06-07
