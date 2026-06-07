import re
from datetime import datetime
from pathlib import Path

import openpyxl

from difal_importacao.models import FornecedorLookup, LinhaApuracaoDifal, PeriodoApuracao

DIFAL_SHEET_RE = re.compile(r"^DIFAL\s+(\d{2})\.(\d{4})\s*$", re.IGNORECASE)

DIFAL_COLUMNS = {
    "FORNECEDOR": "fornecedor_cod",
    "ESTADO": "uf_origem",
    "COD FILIAL": "filial_cod",
    "NOTA FISCAL": "nota_fiscal",
    "CONTA CONTABIL": "conta_contabil",
    "COD PRODUTO": "cod_produto",
    "PRODUTO": "produto_desc",
    "NCM": "ncm",
    "COD FISCAL": "cfop",
    "VALOR CONTÁBIL": "valor_contabil",
    "VALOR ICMS COMPLEMENTAR": "valor_icms_complementar",
    "NOVO DIFAL": "novo_difal",
    "AJUSTE": "ajuste",
}


class DIFALValidationError(Exception):
    pass


def _num(val, default=0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def find_difal_sheet(wb) -> tuple[str, PeriodoApuracao]:
    for name in wb.sheetnames:
        m = DIFAL_SHEET_RE.match(name.strip())
        if m:
            mes, ano = int(m.group(1)), int(m.group(2))
            return name, PeriodoApuracao(mes=mes, ano=ano, label=f"{mes:02d}.{ano}", aba_origem=name)
    raise DIFALValidationError("Aba DIFAL MM.AAAA não encontrada")


def read_difal(path: Path | str, aba: str | None = None) -> tuple[PeriodoApuracao, list[LinhaApuracaoDifal]]:
    path = Path(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if aba:
        if aba not in wb.sheetnames:
            wb.close()
            raise DIFALValidationError(f"Aba '{aba}' não encontrada")
        m = DIFAL_SHEET_RE.match(aba.strip())
        if not m:
            raise DIFALValidationError(f"Aba '{aba}' não corresponde ao padrão DIFAL MM.AAAA")
        periodo = PeriodoApuracao(int(m.group(1)), int(m.group(2)), f"{int(m.group(1)):02d}.{m.group(2)}", aba)
        sheet_name = aba
    else:
        sheet_name, periodo = find_difal_sheet(wb)

    ws = wb[sheet_name]
    hdr = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    col_idx = {str(h).strip(): i for i, h in enumerate(hdr) if h}
    missing = [c for c in DIFAL_COLUMNS if c not in col_idx]
    if missing:
        wb.close()
        raise DIFALValidationError(f"Colunas DIFAL ausentes: {', '.join(missing)}")

    linhas: list[LinhaApuracaoDifal] = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[col_idx["FORNECEDOR"]]:
            continue
        linhas.append(
            LinhaApuracaoDifal(
                fornecedor_cod=str(row[col_idx["FORNECEDOR"]]).strip(),
                uf_origem=str(row[col_idx["ESTADO"]]).strip(),
                filial_cod=str(row[col_idx["COD FILIAL"]]).strip(),
                nota_fiscal=str(row[col_idx["NOTA FISCAL"]]).strip(),
                conta_contabil=str(row[col_idx["CONTA CONTABIL"]]).strip(),
                cod_produto=str(row[col_idx["COD PRODUTO"]]).strip(),
                produto_desc=str(row[col_idx.get("PRODUTO", col_idx["COD PRODUTO"])] or "").strip(),
                ncm=str(row[col_idx.get("NCM", 0)] or "").strip() if "NCM" in col_idx else "",
                cfop=str(row[col_idx["COD FISCAL"]]).strip(),
                valor_contabil=_num(row[col_idx["VALOR CONTÁBIL"]]),
                valor_icms_complementar=_num(row[col_idx["VALOR ICMS COMPLEMENTAR"]]),
                novo_difal=_num(row[col_idx["NOVO DIFAL"]]),
                ajuste=_num(row[col_idx["AJUSTE"]]),
            )
        )
    wb.close()
    return periodo, linhas


def build_chave_rastreio(nota: str, fornecedor: str, produto: str) -> str:
    nota_int = str(int(str(nota).lstrip("0") or "0"))
    return f"{nota_int}{fornecedor}{produto}"


def read_auxiliar_sft(path: Path | str, aba: str = "SFT ") -> dict[str, FornecedorLookup]:
    path = Path(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = aba if aba in wb.sheetnames else aba.strip()
    if sheet not in wb.sheetnames:
        for name in wb.sheetnames:
            if name.strip().upper() == aba.strip().upper():
                sheet = name
                break
        else:
            wb.close()
            return {}

    ws = wb[sheet]
    hdr = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    idx = {str(h): i for i, h in enumerate(hdr) if h}
    lookups: dict[str, FornecedorLookup] = {}

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[idx.get("Cd. Forn", 0)] is None:
            continue
        nota = row[idx.get("Nota Fiscal", 0)]
        forn = str(row[idx["Cd. Forn"]]).strip()
        prod = str(row[idx.get("Cd Produto", 0)]).strip()
        chave = build_chave_rastreio(str(nota), forn, prod)
        lookups[chave] = FornecedorLookup(
            chave_rastreio=chave,
            nome_fornecedor=str(row[idx.get("Nm Forn", "")] or "").strip(),
            loja=str(row[idx.get("Lj. Forn", "0001")] or "0001").zfill(4),
            data_emissao=row[idx["Dt Emissao"]] if isinstance(row[idx.get("Dt Emissao")], datetime) else None,
            data_entrada=row[idx["Dt Entrada"]] if isinstance(row[idx.get("Dt Entrada")], datetime) else None,
            cod_item_contabil=str(row[idx.get("COD ITEM CONTABIL", "")] or "").strip()
            if "COD ITEM CONTABIL" in idx
            else "",
        )
    wb.close()
    return lookups
