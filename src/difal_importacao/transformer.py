from dataclasses import dataclass

from difal_importacao.config import ImportacaoConfig
from difal_importacao.models import (
    FornecedorLookup,
    LancamentoImportacao,
    LinhaApuracaoDifal,
    PeriodoApuracao,
    TotaisConsolidados,
)
from difal_importacao.reader import build_chave_rastreio


@dataclass
class TransformResult:
    lancamentos: list[LancamentoImportacao]
    totais_difal: TotaisConsolidados
    totais_elegiveis: TotaisConsolidados
    excluidas_materialidade: int
    excecoes_conta: int


def is_conta_valida(conta: str) -> bool:
    if not conta or conta in ("#N/A", "#REF!", "*"):
        return False
    return str(conta).replace(".", "").isdigit()


def transform_linha(
    linha: LinhaApuracaoDifal,
    periodo: PeriodoApuracao,
    config: ImportacaoConfig,
    lookup: FornecedorLookup | None = None,
) -> LancamentoImportacao | None:
    if linha.ajuste == 0:
        return None
    if abs(linha.ajuste) < config.limiar_materialidade:
        return None
    if not is_conta_valida(linha.conta_contabil):
        return None

    chave = build_chave_rastreio(linha.nota_fiscal, linha.fornecedor_cod, linha.cod_produto)
    loja = lookup.loja if lookup else "0001"
    nome = lookup.nome_fornecedor if lookup and lookup.nome_fornecedor else linha.fornecedor_cod
    cod_f = f"F{linha.fornecedor_cod}{loja}"

    if linha.ajuste > 0:
        debito, credito = linha.conta_contabil, config.conta_icms_recolher
    else:
        debito, credito = config.conta_icms_recolher, linha.conta_contabil

    nota_display = int(str(linha.nota_fiscal).lstrip("0") or "0")
    historico_base = f"{nota_display}-{nome}"
    historico = historico_base[: config.historico_max_len]

    return LancamentoImportacao(
        loja=loja,
        nota=nota_display,
        nome_fornecedor=nome,
        cod_fornecedor=linha.fornecedor_cod,
        produto=linha.cod_produto,
        cfop=linha.cfop,
        valor_nota=linha.valor_contabil,
        difal=linha.valor_icms_complementar,
        novo_difal=linha.novo_difal,
        ajuste=linha.ajuste,
        chave=chave,
        data_emissao=lookup.data_emissao if lookup else None,
        data_entrada=lookup.data_entrada if lookup else None,
        filial=config.filial,
        debito=debito,
        credito=credito,
        centro_custo=config.centro_custo,
        cod_item_contabil=lookup.cod_item_contabil if lookup else "",
        cod_fornecedor_debito=cod_f,
        cod_fornecedor_credito=cod_f,
        valor_lancamento=round(abs(linha.ajuste), 2),
        historico=historico,
        justificativa=f"AJUSTE FISCAL DIFAL {periodo.label}",
        pendente_enriquecimento=lookup is None or not lookup.nome_fornecedor,
    )


def calc_totais(linhas: list[LinhaApuracaoDifal]) -> TotaisConsolidados:
    t = TotaisConsolidados()
    for l in linhas:
        if l.ajuste == 0:
            continue
        t.total_valor_nota += l.valor_contabil
        t.total_difal += l.valor_icms_complementar
        t.total_novo_difal += l.novo_difal
        t.total_ajuste += l.ajuste
    return t


def gerar_lancamentos(
    linhas: list[LinhaApuracaoDifal],
    periodo: PeriodoApuracao,
    config: ImportacaoConfig,
    lookups: dict[str, FornecedorLookup] | None = None,
) -> TransformResult:
    lookups = lookups or {}
    lancamentos: list[LancamentoImportacao] = []
    excluidas = 0
    excecoes = 0

    for linha in linhas:
        if linha.ajuste == 0:
            continue
        if abs(linha.ajuste) < config.limiar_materialidade:
            excluidas += 1
            continue
        if not is_conta_valida(linha.conta_contabil):
            excecoes += 1
            continue
        chave = build_chave_rastreio(linha.nota_fiscal, linha.fornecedor_cod, linha.cod_produto)
        lanc = transform_linha(linha, periodo, config, lookups.get(chave))
        if lanc:
            lancamentos.append(lanc)

    totais_difal = calc_totais(linhas)
    totais_eleg = TotaisConsolidados()
    for l in lancamentos:
        totais_eleg.total_valor_nota += l.valor_nota
        totais_eleg.total_difal += l.difal
        totais_eleg.total_novo_difal += l.novo_difal
        totais_eleg.total_ajuste += l.ajuste

    return TransformResult(
        lancamentos=lancamentos,
        totais_difal=totais_difal,
        totais_elegiveis=totais_eleg,
        excluidas_materialidade=excluidas,
        excecoes_conta=excecoes,
    )
