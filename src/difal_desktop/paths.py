"""Caminhos da aplicação — desenvolvimento e executável PyInstaller."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def bundle_root() -> Path:
    """Recursos empacotados (configs) dentro do .exe."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def app_root() -> Path:
    """Diretório do projeto ou pasta do executável."""
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    d = app_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_root() -> Path:
    env = os.environ.get("DIFAL_CONFIG_ROOT")
    if env:
        return Path(env)
    bundled = bundle_root() / "config"
    if bundled.exists():
        return bundled
    return app_root() / "config"


def find_referencia_workbook() -> Path | None:
    for base in (app_root(), bundle_root()):
        matches = list(base.glob("*28*.xlsx"))
        if matches:
            return matches[0]
    return None


def logo_path() -> Path | None:
    candidates = (
        bundle_root() / "assets" / "logo_madero.jpeg",
        app_root() / "logo_madero.jpeg",
        app_root() / "assets" / "logo_madero.jpeg",
        bundle_root() / "logo_madero.jpeg",
    )
    for path in candidates:
        if path.exists():
            return path
    return None


def setup_runtime() -> None:
    """Define variáveis usadas pelos módulos de config e job_store."""
    os.environ.setdefault("DIFAL_ROOT", str(app_root()))
    os.environ.setdefault("DIFAL_CONFIG_ROOT", str(config_root()))
    os.environ.setdefault("DIFAL_DATA_ROOT", str(data_root()))
    # Garante cópia gravável de ncm_regras.yaml ao lado do exe/projeto
    from difal_apuracao.ncm_rules import ncm_regras_path

    ncm_regras_path()
