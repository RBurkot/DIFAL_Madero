from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class LinhaBI:
    mes_ano_entrada: datetime | None
    cod_fornecedor: str
    estado: str
    cod_filial: str
    nota_fiscal: str
    cod_produto: str
    produto: str
    ncm: str
    cod_fiscal: str
    quantidade: float
    preco_unitario: float
    total: float
    valor_contabil: float
    aliquota_icms: float
    valor_icms: float
    aliquota_compl: float
    aliquota_icms_complementar: float
    valor_icms_complementar: float
    carga_efetiva_difal: float | None
    d1_icmscom: float
    desc_grupo: str = ""
    desc_tes: str = ""


@dataclass
class LinhaDifal:
    fornecedor: str
    estado: str
    cod_filial: str
    nota_fiscal: str
    conta_contabil: str
    cod_produto: str
    produto: str
    ncm: str
    cod_fiscal: str
    quantidade: float
    preco_unitario: float
    total: float
    desconto: float
    despesas: float
    frete: float
    valor_ipi: float
    icms_retido: float
    valor_contabil: float
    aliquota_icms: float
    valor_icms: float
    aliquota_complementar: float
    aliquota_icms_complementar: float
    valor_icms_complementar: float
    novo_difal: float
    ajuste: float
    metodo_calculo: str = "formula_padrao"
    ncm_regra_aplicada: str = ""
    carga_normativa_ncm: float | None = None
    carga_efetiva_bi: float | None = None
