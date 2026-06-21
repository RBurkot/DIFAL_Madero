from difal_importacao.config import ImportacaoConfig
from difal_importacao.models import FornecedorLookup, LinhaApuracaoDifal, PeriodoApuracao
from difal_importacao.transformer import transform_linha


def _linha_2556(conta: str = "11010020003") -> LinhaApuracaoDifal:
    return LinhaApuracaoDifal(
        fornecedor_cod="123",
        uf_origem="SP",
        filial_cod="01GDIN0004",
        nota_fiscal="000000100",
        conta_contabil=conta,
        cod_produto="P001",
        produto_desc="Produto teste",
        ncm="",
        cfop="2556",
        valor_contabil=100.0,
        valor_icms_complementar=10.0,
        novo_difal=12.0,
        ajuste=2.0,
    )


def test_cod_item_contabil_vem_de_entradas_bi():
    linha = _linha_2556()
    periodo = PeriodoApuracao(5, 2026, "05.2026", "DIFAL 05.2026 ")
    cfg = ImportacaoConfig()
    item_map = {"P001": "ITEM999"}

    lanc = transform_linha(
        linha,
        periodo,
        cfg,
        sb1_map={"P001": "11010020003"},
        item_contabil_map=item_map,
    )

    assert lanc is not None
    assert lanc.cod_item_contabil == "ITEM999"


def test_cod_item_contabil_fallback_sft_quando_sem_entradas():
    linha = _linha_2556()
    periodo = PeriodoApuracao(5, 2026, "05.2026", "DIFAL 05.2026 ")
    cfg = ImportacaoConfig()
    lookup = FornecedorLookup(
        chave_rastreio="100123P001",
        nome_fornecedor="Fornecedor X",
        cod_item_contabil="SFT001",
    )

    lanc = transform_linha(
        linha,
        periodo,
        cfg,
        lookup=lookup,
        sb1_map={"P001": "11010020003"},
        item_contabil_map={},
    )

    assert lanc is not None
    assert lanc.cod_item_contabil == "SFT001"


def test_entradas_bi_tem_prioridade_sobre_sft():
    linha = _linha_2556()
    periodo = PeriodoApuracao(5, 2026, "05.2026", "DIFAL 05.2026 ")
    cfg = ImportacaoConfig()
    lookup = FornecedorLookup(
        chave_rastreio="100123P001",
        nome_fornecedor="Fornecedor X",
        cod_item_contabil="SFT001",
    )

    lanc = transform_linha(
        linha,
        periodo,
        cfg,
        lookup=lookup,
        sb1_map={"P001": "11010020003"},
        item_contabil_map={"P001": "ENTRADAS_AK"},
    )

    assert lanc is not None
    assert lanc.cod_item_contabil == "ENTRADAS_AK"
