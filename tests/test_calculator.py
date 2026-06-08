from difal_apuracao.calculator import (
    _calc_formula_coluna_z,
    _calc_formula_padrao,
    _calc_novo_difal,
    calcular_linha,
)
from difal_apuracao.writer import DIFAL_HEADERS
from difal_apuracao.config import ApuracaoConfig
from difal_apuracao.models import LinhaBI
from difal_apuracao.ncm_rules import load_regras_ncm


def test_formula_padrao_sp_sample():
    novo = _calc_formula_padrao(722, 19.5, 7.5)
    assert abs(novo - 67.2670807453416) < 0.01


def test_formula_padrao_nota_13():
    novo = _calc_formula_padrao(10800, 19.5, 7.5)
    assert abs(novo - 1006.2111801242235) < 0.01


def _linha_base(**kwargs) -> LinhaBI:
    defaults = dict(
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
    defaults.update(kwargs)
    return LinhaBI(**defaults)


def test_ncm_especial_84243010_usa_formula_coluna_z_com_carga_yaml():
    linha = _linha_base(
        ncm="84243010",
        estado="SC",
        valor_contabil=7200,
        valor_icms=864,
        aliquota_icms=12,
        aliquota_compl=19.5,
        aliquota_icms_complementar=7.5,
        carga_efetiva_difal=0,
        d1_icmscom=0,
    )
    regras = load_regras_ncm()
    resultado = _calc_novo_difal(linha, regras)
    esperado = _calc_formula_coluna_z(7200, 864, 8.8)
    assert abs(resultado.novo_difal - esperado) < 0.01
    assert resultado.metodo_calculo == "formula_coluna_z"
    assert resultado.ncm_regra_aplicada == "84243010"
    assert resultado.carga_normativa_ncm == 8.8


def test_ncm_especial_73269090_usa_formula_coluna_z_com_carga_7_yaml():
    linha = _linha_base(
        ncm="73269090",
        estado="SP",
        valor_contabil=1285.5,
        aliquota_icms=12,
        valor_icms=154.26,
        aliquota_compl=19.5,
        aliquota_icms_complementar=7.5,
        carga_efetiva_difal=9.316997277323997,
        d1_icmscom=105.4,
    )
    resultado = _calc_novo_difal(linha, load_regras_ncm())
    assert resultado.metodo_calculo == "formula_coluna_z"
    assert resultado.carga_normativa_ncm == 7.0
    assert abs(resultado.novo_difal - _calc_formula_coluna_z(1285.5, 154.26, 7.0)) < 0.01


def test_formula_coluna_z_ncm_73269090():
    assert abs(_calc_formula_coluna_z(1285.5, 154.26, 7) - (-69.11290322580643)) < 0.01


def test_ncm_metodo_formula_coluna_z_override():
    from difal_apuracao.ncm_rules import RegraNcm

    linha = _linha_base(
        ncm="73269090",
        estado="SP",
        valor_contabil=1285.5,
        valor_icms=154.26,
    )
    regra = RegraNcm(
        ncm="73269090",
        carga_tributaria_pct=7.0,
        ufs_origem=frozenset({"SP"}),
        exclusao_uf=frozenset(),
        tipo="test",
        metodo_novo_difal="formula_coluna_z",
    )
    resultado = _calc_novo_difal(linha, {"73269090": regra})
    assert resultado.metodo_calculo == "formula_coluna_z"
    assert abs(resultado.novo_difal - (-69.11290322580643)) < 0.01


def test_calcular_linha_uses_d1_icmscom():
    out = calcular_linha(_linha_base(), ApuracaoConfig())
    assert abs(out.novo_difal - 1006.2111801242235) < 0.01
    assert out.valor_icms_complementar == 885.47
    assert abs(out.ajuste - (out.novo_difal - 885.47)) < 0.01
    assert out.conta_contabil not in ("#N/A", "#REF!", "")
    assert out.metodo_calculo == "formula_padrao"
    assert out.carga_efetiva_bi == 9.316759


def test_writer_inclui_colunas_auditoria():
    assert "METODO CALCULO" in DIFAL_HEADERS
    assert "NCM REGRA" in DIFAL_HEADERS
    assert "CARGA NORMATIVA NCM" in DIFAL_HEADERS
    assert "CARGA EFETIVA BI" in DIFAL_HEADERS
