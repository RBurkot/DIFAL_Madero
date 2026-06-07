from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PeriodoApuracao:
    mes: int
    ano: int
    label: str
    aba_origem: str


@dataclass
class LinhaApuracaoDifal:
    fornecedor_cod: str
    uf_origem: str
    filial_cod: str
    nota_fiscal: str
    conta_contabil: str
    cod_produto: str
    produto_desc: str
    ncm: str
    cfop: str
    valor_contabil: float
    valor_icms_complementar: float
    novo_difal: float
    ajuste: float


@dataclass
class FornecedorLookup:
    chave_rastreio: str
    nome_fornecedor: str = ""
    loja: str = "0001"
    data_emissao: datetime | None = None
    data_entrada: datetime | None = None
    cod_item_contabil: str = ""


@dataclass
class LancamentoImportacao:
    loja: str
    nota: int | str
    nome_fornecedor: str
    cod_fornecedor: str
    produto: str
    cfop: str
    valor_nota: float
    difal: float
    novo_difal: float
    ajuste: float
    chave: str
    data_emissao: datetime | None
    data_entrada: datetime | None
    filial: str
    debito: str
    credito: str
    centro_custo: str
    cod_item_contabil: str
    cod_fornecedor_debito: str
    cod_fornecedor_credito: str
    valor_lancamento: float
    historico: str
    justificativa: str
    pendente_enriquecimento: bool = False


@dataclass
class TotaisConsolidados:
    total_valor_nota: float = 0.0
    total_difal: float = 0.0
    total_novo_difal: float = 0.0
    total_ajuste: float = 0.0


@dataclass
class RelatorioReconciliacao:
    periodo: str
    linhas_difal_total: int = 0
    linhas_elegiveis: int = 0
    lancamentos_gerados: int = 0
    excluidas_materialidade: int = 0
    excecoes_conta_invalida: int = 0
    divergencias: list[dict] = field(default_factory=list)
    resultado: str = "PENDENTE"
