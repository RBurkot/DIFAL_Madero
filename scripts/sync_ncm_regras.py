"""Gera config/ncm_regras.yaml a partir da Planilha1 da planilha de referência."""
import re
from pathlib import Path

import yaml

try:
    import openpyxl
except ImportError:
    raise SystemExit("openpyxl necessário")

SUDESTE_SUL = ["RS", "SC", "PR", "SP", "RJ", "MG"]


def parse_text(text: str) -> dict:
    text = (text or "").strip()
    carga = None
    m = re.search(r"(\d+[,.]?\d*)\s*%", text)
    if m:
        carga = float(m.group(1).replace(",", "."))

    ufs = None
    exclusao = []
    tipo = "geral"
    if "Sul e Sudeste" in text:
        ufs = SUDESTE_SUL
        exclusao = ["ES"]
        tipo = "interestadual_sul_sudeste"
    elif "Carga tributária" in text:
        tipo = "carga_fixa_descrita"

    return {
        "carga_tributaria_pct": carga,
        "ufs_origem": ufs,
        "exclusao_uf": exclusao,
        "tipo": tipo,
        "metodo_novo_difal": "formula_padrao",
        "vigencia_inicio": None,
        "vigencia_fim": None,
        "observacao": text[:200] if text else "",
    }


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    ref = next(base.glob("*28*.xlsx"))
    wb = openpyxl.load_workbook(ref, read_only=True, data_only=True)
    ws = wb["Planilha1"]
    regras = []
    for row in ws.iter_rows(values_only=True):
        if not row or not row[0] or not row[1]:
            continue
        item = {"ncm": str(row[0]).strip()}
        item.update(parse_text(str(row[1])))
        regras.append(item)
    wb.close()

    out = base / "config" / "ncm_regras.yaml"
    header = (
        "# Gerado por scripts/sync_ncm_regras.py — não editar manualmente se for re-sincronizar.\n"
        "# metodo_novo_difal padrão: formula_padrao (validado na aba DIFAL de referência).\n\n"
    )
    content = header + yaml.dump({"regras": regras}, allow_unicode=True, sort_keys=False)
    out.write_text(content, encoding="utf-8")
    print(f"Escrito {len(regras)} regras em {out}")


if __name__ == "__main__":
    main()
