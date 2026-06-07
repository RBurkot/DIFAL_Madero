from difal_apuracao.calculator import _calc_novo_difal, calcular_linha
from difal_apuracao.config import ApuracaoConfig
from difal_apuracao.models import LinhaBI


def test_novo_difal_formula_sp_sample():
    # VC=722, aliq_compl=19.5, aliq_icms_compl=7.5 → 67.267...
    novo = _calc_novo_difal(722, 19.5, 7.5)
    assert abs(novo - 67.2670807453416) < 0.01


def test_novo_difal_formula_nota_13():
    novo = _calc_novo_difal(10800, 19.5, 7.5)
    assert abs(novo - 1006.2111801242235) < 0.01


def test_calcular_linha_uses_d1_icmscom():
    linha = LinhaBI(
        mes_ano_entrada=None,
        cod_fornecedor="221235",
        estado="SP",
        cod_filial="01GDIN0004",
        nota_fiscal="13",
        cod_produto="10724305001300",
        produto="TEST",
        ncm="85334099",
        cod_fiscal="2556",
        quantidade=1,
        preco_unitario=10800,
        total=10800,
        valor_contabil=10800,
        aliquota_icms=12,
        valor_icms=1296,
        aliquota_compl=19.5,
        aliquota_icms_complementar=7.5,
        valor_icms_complementar=1006.21,
        carga_efetiva_difal=9.316759,
        d1_icmscom=885.47,
        desc_grupo="PECAS EQUIPAMENTOS",
    )
    cfg = ApuracaoConfig()
    out = calcular_linha(linha, cfg)
    assert abs(out.novo_difal - 1006.2111801242235) < 0.01
    assert out.valor_icms_complementar == 885.47
    assert abs(out.ajuste - (out.novo_difal - 885.47)) < 0.01
    assert out.conta_contabil not in ("#N/A", "#REF!", "")
