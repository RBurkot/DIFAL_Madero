"""Regras NCM normalizadas (config/ncm_regras.yaml)."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

MetodoNovoDifal = Literal["formula_padrao", "formula_coluna_z", "carga_bi", "carga_tributaria"]

SUDESTE_SUL = frozenset({"RS", "SC", "PR", "SP", "RJ", "MG"})


@dataclass(frozen=True)
class RegraNcm:
    ncm: str
    carga_tributaria_pct: float | None
    ufs_origem: frozenset[str] | None
    exclusao_uf: frozenset[str]
    tipo: str
    metodo_novo_difal: MetodoNovoDifal
    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None
    observacao: str = ""


def _bundle_ncm_path() -> Path:
    if os.environ.get("DIFAL_CONFIG_ROOT"):
        p = Path(os.environ["DIFAL_CONFIG_ROOT"]) / "ncm_regras.yaml"
        if p.exists():
            return p
    root = Path(__file__).resolve().parents[2]
    return root / "config" / "ncm_regras.yaml"


def _app_root() -> Path:
    if os.environ.get("DIFAL_ROOT"):
        return Path(os.environ["DIFAL_ROOT"])
    return Path(__file__).resolve().parents[2]


def ncm_regras_path() -> Path:
    """Caminho gravável do arquivo de regras (prioriza config ao lado do exe/projeto)."""
    user_dir = _app_root() / "config"
    user_dir.mkdir(parents=True, exist_ok=True)
    user_path = user_dir / "ncm_regras.yaml"
    bundled = _bundle_ncm_path()
    if not user_path.exists() and bundled.exists():
        shutil.copy2(bundled, user_path)
    return user_path


def _parse_date(val: Any) -> date | None:
    if val is None or val == "":
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _format_date_iso(d: date | None) -> str | None:
    return d.isoformat() if d else None


def _item_to_regra(item: dict[str, Any]) -> RegraNcm:
    ncm = str(item["ncm"]).strip()
    ufs = item.get("ufs_origem")
    return RegraNcm(
        ncm=ncm,
        carga_tributaria_pct=float(item["carga_tributaria_pct"]) if item.get("carga_tributaria_pct") is not None else None,
        ufs_origem=frozenset(str(u).strip().upper() for u in ufs) if ufs else None,
        exclusao_uf=frozenset(str(u).strip().upper() for u in item.get("exclusao_uf") or []),
        tipo=str(item.get("tipo", "")),
        metodo_novo_difal=item.get("metodo_novo_difal", "formula_coluna_z"),
        vigencia_inicio=_parse_date(item.get("vigencia_inicio")),
        vigencia_fim=_parse_date(item.get("vigencia_fim")),
        observacao=str(item.get("observacao", "")),
    )


def regra_vigente(regra: RegraNcm, data_referencia: date | None) -> bool:
    if data_referencia is None:
        return True
    if regra.vigencia_inicio and data_referencia < regra.vigencia_inicio:
        return False
    if regra.vigencia_fim and data_referencia > regra.vigencia_fim:
        return False
    return True


def load_regras_ncm_raw(path: Path | str | None = None) -> list[dict[str, Any]]:
    path = Path(path or ncm_regras_path())
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("regras", []))


def load_regras_ncm(
    path: Path | str | None = None,
    data_referencia: date | None = None,
) -> dict[str, RegraNcm]:
    regras: dict[str, RegraNcm] = {}
    for item in load_regras_ncm_raw(path):
        regra = _item_to_regra(item)
        if regra_vigente(regra, data_referencia):
            regras[regra.ncm] = regra
    return regras


def save_regras_ncm(regras: list[dict[str, Any]], path: Path | str | None = None) -> Path:
    path = Path(path or ncm_regras_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Regras fiscais por NCM — editável pela interface desktop.\n"
        "# vigencia_fim: null = sem data de encerramento (YYYY-MM-DD ou DD/MM/AAAA).\n\n"
    )
    body = yaml.dump({"regras": regras}, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(header + body, encoding="utf-8")
    return path


def regra_to_dict(regra: RegraNcm) -> dict[str, Any]:
    return {
        "ncm": regra.ncm,
        "carga_tributaria_pct": regra.carga_tributaria_pct,
        "ufs_origem": sorted(regra.ufs_origem) if regra.ufs_origem else None,
        "exclusao_uf": sorted(regra.exclusao_uf) if regra.exclusao_uf else [],
        "tipo": regra.tipo,
        "metodo_novo_difal": regra.metodo_novo_difal,
        "vigencia_inicio": _format_date_iso(regra.vigencia_inicio),
        "vigencia_fim": _format_date_iso(regra.vigencia_fim),
        "observacao": regra.observacao or None,
    }


def regra_aplicavel(
    ncm: str,
    uf_origem: str,
    regras: dict[str, RegraNcm],
    data_referencia: date | None = None,
) -> RegraNcm | None:
    regra = regras.get(str(ncm).strip())
    if not regra:
        return None
    if not regra_vigente(regra, data_referencia):
        return None

    uf = str(uf_origem).strip().upper()
    if uf in regra.exclusao_uf:
        return None

    if regra.ufs_origem is None:
        return regra

    if uf in regra.ufs_origem:
        return regra

    return None


def data_referencia_linha(mes_ano_entrada: datetime | None) -> date | None:
    if isinstance(mes_ano_entrada, datetime):
        return mes_ano_entrada.date()
    return None
