from dataclasses import dataclass
from pathlib import Path

from difal_apuracao.sb1_lookup import (
    _find_sb1_workbook,
    load_sb1_contas,
    normalize_cfop,
    normalize_codigo,
)
from difal_importacao.config import ImportacaoConfig
from difal_importacao.models import (
    FornecedorLookup,
    LancamentoImportacao,
    LinhaApuracaoDifal,
    PeriodoApuracao,
    TotaisConsolidados,
)
from difal_importacao.entradas_bi_lookup import load_entradas_map
from difal_importacao.reader import build_chave_rastreio, lookup_fornecedor_by_chave


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


def load_sb1_map(
    config: ImportacaoConfig,
    sb1_workbook: Path | str | None = None,
) -> dict[str, str]:
    explicit = Path(sb1_workbook) if sb1_workbook else None
    if explicit is None and config.sb1_workbook:
        explicit = Path(config.sb1_workbook)
    wb_path = _find_sb1_workbook(explicit)
    if not wb_path:
        return {}
    return load_sb1_contas(str(wb_path))


def resolve_debito_credito(
    cfop: str,
    ajuste: float,
    config: ImportacaoConfig,
    *,
    conta_contabil: str = "",
    cod_produto: str = "",
    sb1_map: dict[str, str] | None = None,
) -> tuple[str, str] | None:
    icms = config.conta_icms_recolher
    cfop_norm = normalize_cfop(cfop)

    if cfop_norm == "2551":
        imob = config.conta_imobilizado_2551
        if ajuste >= 0:
            return imob, icms
        return icms, imob

    if cfop_norm == "2556":
        prod = normalize_codigo(cod_produto)
        conta_sb1 = (sb1_map or {}).get(prod, "")
        if not is_conta_valida(conta_sb1) and is_conta_valida(conta_contabil):
            conta_sb1 = conta_contabil
        if not is_conta_valida(conta_sb1):
            return None
        if ajuste >= 0:
            return conta_sb1, icms
        return icms, conta_sb1

    if not is_conta_valida(conta_contabil):
        return None
    if ajuste >= 0:
        return conta_contabil, icms
    return icms, conta_contabil


def transform_linha(
    linha: LinhaApuracaoDifal,
    periodo: PeriodoApuracao,
    config: ImportacaoConfig,
    lookup: FornecedorLookup | None = None,
    lookups: dict[str, FornecedorLookup] | None = None,
    sb1_map: dict[str, str] | None = None,
    item_contabil_map: dict[str, str] | None = None,
) -> LancamentoImportacao | None:
    if linha.ajuste == 0:
        return None
    if abs(linha.ajuste) < config.limiar_materialidade:
        return None

    contas = resolve_debito_credito(
        linha.cfop,
        linha.ajuste,
        config,
        conta_contabil=linha.conta_contabil,
        cod_produto=linha.cod_produto,
        sb1_map=sb1_map,
    )
    if not contas:
        return None
    debito, credito = contas

    chave = build_chave_rastreio(linha.nota_fiscal, linha.fornecedor_cod, linha.cod_produto)
    if lookup is None and lookups:
        lookup = lookup_fornecedor_by_chave(lookups, chave)
    loja = lookup.loja if lookup else "0001"
    nome = lookup.nome_fornecedor if lookup and lookup.nome_fornecedor else linha.fornecedor_cod
    cod_f = f"F{linha.fornecedor_cod}{loja}"

    nota_display = int(str(linha.nota_fiscal).lstrip("0") or "0")
    historico_base = f"{nota_display}-{nome}"
    historico = historico_base[: config.historico_max_len]

    prod = normalize_codigo(linha.cod_produto)
    cod_item = (item_contabil_map or {}).get(prod, "")
    if not cod_item and lookup and lookup.cod_item_contabil:
        cod_item = lookup.cod_item_contabil

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
        cod_item_contabil=cod_item,
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
    sb1_workbook: Path | str | None = None,
    entradas_workbook: Path | str | None = None,
) -> TransformResult:
    lookups = lookups or {}
    has_2556 = any(normalize_cfop(l.cfop) == "2556" for l in linhas)
    sb1_map = load_sb1_map(config, sb1_workbook) if has_2556 else {}
    item_contabil_map = load_entradas_map(entradas_workbook, sb1_workbook)
    lancamentos: list[LancamentoImportacao] = []
    excluidas = 0
    excecoes = 0

    for linha in linhas:
        if linha.ajuste == 0:
            continue
        if abs(linha.ajuste) < config.limiar_materialidade:
            excluidas += 1
            continue
        chave = build_chave_rastreio(linha.nota_fiscal, linha.fornecedor_cod, linha.cod_produto)
        lanc = transform_linha(
            linha,
            periodo,
            config,
            lookups=lookups,
            sb1_map=sb1_map,
            item_contabil_map=item_contabil_map,
        )
        if lanc:
            lancamentos.append(lanc)
        else:
            excecoes += 1

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
