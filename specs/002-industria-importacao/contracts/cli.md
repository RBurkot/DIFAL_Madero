# CLI Contract: difal-importacao

## Command

```text
difal-importacao gerar <workbook_entrada> [OPTIONS]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `workbook_entrada` | yes | Caminho do `.xlsx` contendo aba `DIFAL MM.AAAA` |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--aba-difal` | `-d` | auto-detect | Nome da aba DIFAL (regex `DIFAL \d{2}\.\d{4}`) |
| `--saida` | `-o` | `<entrada>_importacao.xlsx` | Caminho do workbook de saída |
| `--config` | `-c` | `config/importacao.yaml` | Configuração de contas e limiar |
| `--aba-auxiliar` | `-a` | `SFT` | Aba para enriquecimento (ou `BI QLVIEW`) |
| `--sem-enriquecimento` | | false | Ignora lookup de nome/datas |
| `--reconciliar` | `-r` | none | Caminho da planilha referência para diff |
| `--relatorio` | | `reconciliacao.json` | Saída do relatório de reconciliação |
| `--verbose` | `-v` | false | Log operacional (sem valores fiscais completos) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Sucesso; lançamentos gerados |
| 1 | Erro de validação (aba ausente, colunas faltando) |
| 2 | Erro de processamento (arquivo corrompido, I/O) |
| 3 | Reconciliação falhou (divergências acima da tolerância) |

## stdout (human)

```text
Período: 05/2026
Linhas DIFAL: 346
Lançamentos gerados: 196
Excluídas (materialidade): 127
Exceções (conta inválida): 3
Saída: C:\...\saida_importacao.xlsx
Relatório: C:\...\reconciliacao.json
```

## stdout (JSON, `--json`)

```json
{
  "periodo": "05.2026",
  "linhas_difal": 346,
  "lancamentos_gerados": 196,
  "saida": "path/to/output.xlsx",
  "reconciliacao": "path/to/reconciliacao.json",
  "sucesso": true
}
```
