from datetime import datetime

from difal_importacao.models import LancamentoImportacao, TotaisConsolidados
from difal_importacao.writer import format_data_br, write_importacao_sheet


def test_format_data_br():
    assert format_data_br(datetime(2026, 5, 10)) == "10/05/2026"
    assert format_data_br(None) is None


def test_writer_exporta_datas_dd_mm_aaaa(tmp_path):
    emissao = datetime(2026, 5, 10)
    entrada = datetime(2026, 5, 15)
    lanc = LancamentoImportacao(
        loja="0001",
        nota=100,
        nome_fornecedor="Fornecedor",
        cod_fornecedor="123",
        produto="P001",
        cfop="2556",
        valor_nota=100.0,
        difal=10.0,
        novo_difal=12.0,
        ajuste=2.0,
        chave="100123P001",
        data_emissao=emissao,
        data_entrada=entrada,
        filial="01GDIN0004",
        debito="11010020003",
        credito="20140010007",
        centro_custo="290001",
        cod_item_contabil="ITEM1",
        cod_fornecedor_debito="F1230001",
        cod_fornecedor_credito="F1230001",
        valor_lancamento=2.0,
        historico="100-Fornecedor",
        justificativa="AJUSTE FISCAL DIFAL 05.2026",
    )
    out = tmp_path / "out.xlsx"
    write_importacao_sheet([lanc], TotaisConsolidados(), out)

    import openpyxl

    wb = openpyxl.load_workbook(out, data_only=True)
    ws = wb["INDUSTRIA-IMPORTAÇÃO"]
    row = list(ws.iter_rows(min_row=5, max_row=5, values_only=True))[0]
    assert ws.auto_filter.ref is not None
    assert ws.auto_filter.ref.startswith("A4:")
    wb.close()

    assert row[11] == "10/05/2026"  # L DATA EMISSAO
    assert row[12] == "15/05/2026"  # M DATA ENTRADA
    assert row[25] == "10/05/2026"  # Z DATA EMISSÃO
    assert row[26] == "15/05/2026"  # AA DATA CONTABILIZAÇÃO
