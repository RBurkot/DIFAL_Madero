from pathlib import Path

import openpyxl
from openpyxl import Workbook

from difal_importacao.models import LancamentoImportacao, TotaisConsolidados

IMPORT_HEADERS = [
    "LOJA", "NOTA", "NOME FORNE", "COD FORNECEDOR", "PRODUTO", "CFOP",
    "VALOR DA NOTA", "DIFAL", "NOVO DIFAL", "AJUSTE", "Chave",
    "DATA EMISSAO", "DATA ENTRADA", "FILIAL", "DÉBITO", "CENTRO DE CUSTO",
    "COD ITEM CONTABIL", "COD FORNECEDOR", "CRÉDITO", "CENTRO DE CUSTO",
    "COD ITEM CONTABIL", "COD FORNECEDOR", "VALOR", "HISTÓRICO",
    "JUSTIFICATIVA", "DATA EMISSÃO", "DATA CONTABILIZAÇÃO",
]


def write_importacao_sheet(
    lancamentos: list[LancamentoImportacao],
    totais: TotaisConsolidados,
    output: Path | str,
    source_workbook: Path | str | None = None,
) -> Path:
    output = Path(output)
    if source_workbook and Path(source_workbook).exists():
        wb = openpyxl.load_workbook(source_workbook)
    else:
        wb = Workbook()
        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]

    if "INDUSTRIA-IMPORTAÇÃO" in wb.sheetnames:
        del wb["INDUSTRIA-IMPORTAÇÃO"]
    ws = wb.create_sheet("INDUSTRIA-IMPORTAÇÃO")

    ws.append([None] * 27)
    row2 = [None] * 27
    row2[6] = totais.total_valor_nota
    row2[7] = totais.total_difal
    row2[8] = totais.total_novo_difal
    row2[9] = totais.total_ajuste
    ws.append(row2)
    ws.append([None] * 27)
    ws.append(IMPORT_HEADERS)

    for l in lancamentos:
        ws.append([
            l.loja, l.nota, l.nome_fornecedor, l.cod_fornecedor, l.produto, l.cfop,
            l.valor_nota, l.difal, l.novo_difal, l.ajuste, l.chave,
            l.data_emissao, l.data_entrada, l.filial,
            l.debito, l.centro_custo, l.cod_item_contabil, l.cod_fornecedor_debito,
            l.credito, l.centro_custo, l.cod_item_contabil, l.cod_fornecedor_credito,
            l.valor_lancamento, l.historico, l.justificativa,
            l.data_emissao, l.data_entrada,
        ])

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    wb.close()
    return output
