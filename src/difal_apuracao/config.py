import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ApuracaoConfig(BaseModel):
    aliquota_interna_pr: float = 19.5
    filial: str = "01GDIN0004"
    cfops_escopo: list[str] = Field(default_factory=lambda: ["2551", "2556", "2407"])
    sb1_workbook: str | None = None
    ncm_carga_especial: dict[str, dict[str, Any]] = Field(default_factory=dict)
    conta_por_cfop: dict[str, str | None] = Field(default_factory=dict)
    conta_por_grupo: dict[str, str] = Field(default_factory=dict)


def _config_dir() -> Path:
    if os.environ.get("DIFAL_CONFIG_ROOT"):
        return Path(os.environ["DIFAL_CONFIG_ROOT"])
    return _project_root() / "config"


def _project_root() -> Path:
    if os.environ.get("DIFAL_CONFIG_ROOT"):
        return Path(os.environ["DIFAL_CONFIG_ROOT"]).parent
    if os.environ.get("DIFAL_ROOT"):
        return Path(os.environ["DIFAL_ROOT"])
    return Path(__file__).resolve().parents[2]


def load_config(path: Path | str | None = None) -> ApuracaoConfig:
    config_dir = _config_dir()
    if path is None:
        path = config_dir / "apuracao.yaml"
    path = Path(path)
    data: dict[str, Any] = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    grupo_path = config_dir / "conta_por_grupo.yaml"
    if grupo_path.exists():
        grupo_data = yaml.safe_load(grupo_path.read_text(encoding="utf-8")) or {}
        if isinstance(grupo_data, dict):
            data.setdefault("conta_por_grupo", {}).update(grupo_data)

    return ApuracaoConfig.model_validate(data)
