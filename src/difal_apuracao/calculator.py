"""Cálculo DIFAL a partir do extrato BI."""
from difal_apuracao.config import ApuracaoConfig
from difal_apuracao.models import LinhaBI, LinhaDifal
from difal_apuracao.sb1_lookup import resolve_conta_produto


def _as_percent(value: float) -> float:
    return value * 100 if 0 < value <= 1 else value


def _calc_novo_difal(valor_contabil: float, aliquota_compl: float, aliquota_icms_compl: float) -> float:
    """Fórmula da planilha de referência: =R/((100-U)/100)*V%."""
    aliq_compl = _as_percent(aliquota_compl)
    aliq_icms_compl = _as_percent(aliquota_icms_compl)
    if aliq_compl >= 100:
        return 0.0
    return valor_contabil / ((100 - aliq_compl) / 100) * (aliq_icms_compl / 100)


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
    novo_difal = _calc_novo_difal(linha.valor_contabil, linha.aliquota_compl, linha.aliquota_icms_complementar)
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
    )


def calcular_apuracao(linhas: list[LinhaBI], config: ApuracaoConfig) -> list[LinhaDifal]:
    return [calcular_linha(l, config) for l in linhas]
