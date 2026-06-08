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
    memoria_calculo: str = ""


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


def _fmt_valor(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_pct(value: float) -> str:
    pct = _as_percent(value)
    s = f"{pct:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _memoria_formula_coluna_z(
    linha: LinhaBI,
    ncm: str,
    carga_pct: float,
    novo: float,
) -> str:
    carga = _as_percent(carga_pct) / 100.0
    vc, vi = linha.valor_contabil, linha.valor_icms
    base = (vc - vi) / (1.0 - carga) if carga < 1 else 0.0
    return " | ".join([
        f"NCM {ncm} | metodo formula_coluna_z | carga normativa {_fmt_pct(carga_pct)}% (ncm_regras.yaml)",
        f"Base = (VC - VI) / (1 - carga) = ({_fmt_valor(vc)} - {_fmt_valor(vi)}) / (1 - {_fmt_pct(carga_pct)}%) = {_fmt_valor(base)}",
        f"NOVO DIFAL = Base x carga - VI = {_fmt_valor(base)} x {_fmt_pct(carga_pct)}% - {_fmt_valor(vi)} = {_fmt_valor(novo)}",
    ])


def _memoria_formula_padrao(linha: LinhaBI, ncm: str | None, novo: float) -> str:
    u = _as_percent(linha.aliquota_compl)
    v = _as_percent(linha.aliquota_icms_complementar)
    vc = linha.valor_contabil
    divisor = (100 - u) / 100
    prefix = f"NCM {ncm} | " if ncm else ""
    return " | ".join([
        f"{prefix}metodo formula_padrao (base dupla)",
        f"NOVO DIFAL = VC / ((100-U)/100) x V% = {_fmt_valor(vc)} / {divisor:.4f} x {_fmt_pct(v)}% = {_fmt_valor(novo)}",
    ])


def _memoria_carga_tributaria(linha: LinhaBI, ncm: str, carga_pct: float, novo: float) -> str:
    vc = linha.valor_contabil
    return " | ".join([
        f"NCM {ncm} | metodo carga_tributaria | carga {_fmt_pct(carga_pct)}% (ncm_regras.yaml)",
        f"NOVO DIFAL = VC x carga = {_fmt_valor(vc)} x {_fmt_pct(carga_pct)}% = {_fmt_valor(novo)}",
    ])


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
    metodo_config = regra.metodo_novo_difal if regra else "formula_padrao"

    if (
        regra
        and carga_norm is not None
        and metodo_config not in ("formula_padrao", "carga_tributaria")
    ):
        novo = _calc_formula_coluna_z(linha.valor_contabil, linha.valor_icms, carga_norm)
        return ResultadoCalculo(
            novo_difal=novo,
            metodo_calculo="formula_coluna_z",
            ncm_regra_aplicada=ncm_regra,
            carga_normativa_ncm=carga_norm,
            memoria_calculo=_memoria_formula_coluna_z(linha, ncm_regra, carga_norm, novo),
        )

    if metodo_config == "carga_tributaria" and regra and regra.carga_tributaria_pct is not None:
        novo = linha.valor_contabil * regra.carga_tributaria_pct / 100.0
        return ResultadoCalculo(
            novo_difal=novo,
            metodo_calculo="carga_tributaria",
            ncm_regra_aplicada=ncm_regra,
            carga_normativa_ncm=carga_norm,
            memoria_calculo=_memoria_carga_tributaria(linha, ncm_regra, regra.carga_tributaria_pct, novo),
        )

    metodo = "formula_padrao_ncm" if regra else "formula_padrao"
    novo = _calc_formula_padrao(
        linha.valor_contabil, linha.aliquota_compl, linha.aliquota_icms_complementar
    )
    return ResultadoCalculo(
        novo_difal=novo,
        metodo_calculo=metodo,
        ncm_regra_aplicada=ncm_regra,
        carga_normativa_ncm=carga_norm,
        memoria_calculo=_memoria_formula_padrao(linha, ncm_regra or None, novo),
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
        memoria_calculo=resultado.memoria_calculo,
    )


def calcular_apuracao(linhas: list[LinhaBI], config: ApuracaoConfig) -> list[LinhaDifal]:
    return [calcular_linha(l, config) for l in linhas]
