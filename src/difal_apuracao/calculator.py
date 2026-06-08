"""Cálculo DIFAL a partir do extrato BI."""
from dataclasses import dataclass

from difal_apuracao.config import ApuracaoConfig
from difal_apuracao.models import LinhaBI, LinhaDifal
from difal_apuracao.ncm_rules import (
    RegraNcm,
    data_referencia_linha,
    load_regras_ncm,
    regra_aplicavel,
)
from difal_apuracao.sb1_lookup import resolve_conta_produto


@dataclass
class ResultadoCalculo:
    novo_difal: float
    metodo_calculo: str
    ncm_regra_aplicada: str
    carga_normativa_ncm: float | None
    carga_efetiva_bi: float | None


def _as_percent(value: float) -> float:
    return value * 100 if 0 < value <= 1 else value


def _calc_formula_padrao(valor_contabil: float, aliquota_compl: float, aliquota_icms_compl: float) -> float:
    """Base dupla (col. NOVO DIFAL da planilha): =R/((100-U)/100)*V%."""
    aliq_compl = _as_percent(aliquota_compl)
    aliq_icms_compl = _as_percent(aliquota_icms_compl)
    if aliq_compl >= 100:
        return 0.0
    return valor_contabil / ((100 - aliq_compl) / 100) * (aliq_icms_compl / 100)


def _calc_formula_coluna_z(
    valor_contabil: float,
    valor_icms: float,
    carga_tributaria_pct: float,
) -> float:
    """
    Col. Z da planilha de referência para NCM com benefício:

    (((R-T)/(1-carga))*carga)-T

    `carga` = carga_tributaria_pct do config/ncm_regras.yaml (ex.: 7,0 ou 8,8).
    """
    carga = _as_percent(carga_tributaria_pct) / 100.0
    if carga >= 1:
        return 0.0
    return ((valor_contabil - valor_icms) / (1.0 - carga)) * carga - valor_icms


def _auditoria_ncm(regra: RegraNcm | None) -> tuple[str, float | None]:
    if not regra:
        return "", None
    return regra.ncm, regra.carga_tributaria_pct


def _calc_novo_difal(linha: LinhaBI, regras_ncm: dict | None = None) -> ResultadoCalculo:
    """
    Prioridade do novo_difal:

    1. formula_coluna_z — NCM com benefício (padrão): carga de ncm_regras.yaml
       (((VC−VI)/(1−carga/100))*carga/100)−VI
    2. carga_tributaria — override explícito na regra NCM
    3. formula_padrao — base dupla quando metodo=formula_padrao ou sem regra NCM
    """
    data_ref = data_referencia_linha(linha.mes_ano_entrada)
    regras_ncm = regras_ncm if regras_ncm is not None else load_regras_ncm(data_referencia=data_ref)
    regra = regra_aplicavel(linha.ncm, linha.estado, regras_ncm, data_ref)
    ncm_regra, carga_norm = _auditoria_ncm(regra)
    carga_bi = linha.carga_efetiva_difal if linha.carga_efetiva_difal and linha.carga_efetiva_difal > 0 else None
    metodo_config = regra.metodo_novo_difal if regra else "formula_padrao"

    if (
        regra
        and carga_norm is not None
        and metodo_config not in ("formula_padrao", "carga_tributaria")
    ):
        return ResultadoCalculo(
            novo_difal=_calc_formula_coluna_z(
                linha.valor_contabil, linha.valor_icms, carga_norm
            ),
            metodo_calculo="formula_coluna_z",
            ncm_regra_aplicada=ncm_regra,
            carga_normativa_ncm=carga_norm,
            carga_efetiva_bi=carga_bi,
        )

    if metodo_config == "carga_tributaria" and regra and regra.carga_tributaria_pct is not None:
        return ResultadoCalculo(
            novo_difal=linha.valor_contabil * regra.carga_tributaria_pct / 100.0,
            metodo_calculo="carga_tributaria",
            ncm_regra_aplicada=ncm_regra,
            carga_normativa_ncm=carga_norm,
            carga_efetiva_bi=carga_bi,
        )

    metodo = "formula_padrao_ncm" if regra else "formula_padrao"
    return ResultadoCalculo(
        novo_difal=_calc_formula_padrao(
            linha.valor_contabil, linha.aliquota_compl, linha.aliquota_icms_complementar
        ),
        metodo_calculo=metodo,
        ncm_regra_aplicada=ncm_regra,
        carga_normativa_ncm=carga_norm,
        carga_efetiva_bi=carga_bi,
    )


def _resolve_conta(linha: LinhaBI, config: ApuracaoConfig) -> str:
    return resolve_conta_produto(
        linha.cod_produto,
        sb1_workbook=config.sb1_workbook,
        conta_por_grupo=config.conta_por_grupo,
        grupo=linha.desc_grupo,
        conta_por_cfop=config.conta_por_cfop,
        cfop=linha.cod_fiscal,
    )


def calcular_linha(linha: LinhaBI, config: ApuracaoConfig) -> LinhaDifal:
    resultado = _calc_novo_difal(linha)
    novo_difal = resultado.novo_difal
    valor_icms_complementar = linha.d1_icmscom
    ajuste = novo_difal - valor_icms_complementar

    aliq_icms = linha.aliquota_icms
    if aliq_icms > 1:
        aliq_icms_frac = aliq_icms / 100.0
    else:
        aliq_icms_frac = aliq_icms

    return LinhaDifal(
        fornecedor=linha.cod_fornecedor,
        estado=linha.estado,
        cod_filial=linha.cod_filial or config.filial,
        nota_fiscal=str(linha.nota_fiscal).zfill(9) if linha.nota_fiscal.isdigit() else linha.nota_fiscal,
        conta_contabil=_resolve_conta(linha, config),
        cod_produto=linha.cod_produto,
        produto=linha.produto,
        ncm=linha.ncm,
        cod_fiscal=linha.cod_fiscal,
        quantidade=linha.quantidade,
        preco_unitario=linha.preco_unitario,
        total=linha.total,
        desconto=0.0,
        despesas=0.0,
        frete=0.0,
        valor_ipi=0.0,
        icms_retido=0.0,
        valor_contabil=linha.valor_contabil,
        aliquota_icms=aliq_icms_frac,
        valor_icms=linha.valor_icms,
        aliquota_complementar=linha.aliquota_compl,
        aliquota_icms_complementar=linha.aliquota_icms_complementar,
        valor_icms_complementar=valor_icms_complementar,
        novo_difal=novo_difal,
        ajuste=ajuste,
        metodo_calculo=resultado.metodo_calculo,
        ncm_regra_aplicada=resultado.ncm_regra_aplicada,
        carga_normativa_ncm=resultado.carga_normativa_ncm,
        carga_efetiva_bi=resultado.carga_efetiva_bi,
    )


def calcular_apuracao(linhas: list[LinhaBI], config: ApuracaoConfig) -> list[LinhaDifal]:
    return [calcular_linha(l, config) for l in linhas]
