# UI Screens Contract

## Screen 1: Home (`/`)

**Purpose**: Seleção de arquivos, período e modo de execução (US1)

| Element | Behavior |
|---------|----------|
| FilePicker BI | Aceita `.xlsx`; chama POST /uploads; exibe badge válido/inválido |
| FilePicker DIFAL | Visível quando modo ≠ `completo`; opcional em `somente_importacao` |
| PeriodForm | Mês/ano (MM/AAAA); corte dia opcional (1–31) |
| Modo select | `completo` \| `somente_apuracao` \| `somente_importacao` |
| Botão Iniciar | Habilitado só se uploads válidos + período; POST /jobs → redirect `/jobs/{id}` |
| JobHistory | Lista últimas 10 execuções com status e link para resultado |

**Validation feedback**: lista de erros de layout abaixo de cada file picker

## Screen 2: Processing (`/jobs/:id`)

**Purpose**: Acompanhamento de etapas (US2)

| Element | Behavior |
|---------|----------|
| PipelineStepper | 4 etapas: Validação → Apuração DIFAL → INDUSTRIA-IMPORTAÇÃO → Reconciliação |
| Progress bar | Por etapa ativa; % e contadores de `step_progress` SSE |
| Log resumido | Últimas 5 mensagens de etapa (sem valores fiscais) |
| Status badge | Em processamento / Concluído / Erro |
| Auto-redirect | Para `/jobs/:id/result` em `job_completed` |

**Error state**: etapa vermelha + `error_summary` + botão "Voltar ao início"

## Screen 3: Result (`/jobs/:id/result`)

**Purpose**: Resumo e download (US3)

| Element | Behavior |
|---------|----------|
| Resumo cards | Período, linhas, lançamentos, totais consolidados |
| Reconciliação badge | Verde/amarelo/vermelho conforme status |
| Alertas list | Conta inválida, materialidade, etc. |
| Download buttons | Um por artifact disponível |
| Export relatório | JSON de reconciliação |
| Nova execução | Link para `/` |

**Ressalvas**: downloads habilitados mesmo com `APROVADO_COM_RESSALVAS` ou `REPROVADO`

## Global

- Idioma: pt-BR
- Título app: "DIFAL Indústria — Madero"
- Cores status: success `#16a34a`, warning `#ca8a04`, error `#dc2626`
- Responsivo: mínimo 1024px (desktop corporativo)
