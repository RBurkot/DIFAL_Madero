import os
from pathlib import Path

import yaml
from pydantic import BaseModel


class ImportacaoConfig(BaseModel):
    limiar_materialidade: float = 0.01
    conta_icms_recolher: str = "20140010007"
    conta_imobilizado_2551: str = "12050010100"
    sb1_workbook: str | None = None
    centro_custo: str = "290001"
    filial: str = "01GDIN0004"
    historico_max_len: int = 28
    tolerancia_linha: float = 0.01
    tolerancia_total: float = 1.00


def load_config(path: Path | str | None = None) -> ImportacaoConfig:
    if path is None:
        if os.environ.get("DIFAL_CONFIG_ROOT"):
            path = Path(os.environ["DIFAL_CONFIG_ROOT"]) / "importacao.yaml"
        else:
            root = Path(os.environ.get("DIFAL_ROOT", Path(__file__).resolve().parents[2]))
            path = root / "config" / "importacao.yaml"
    path = Path(path)
    if not path.exists():
        return ImportacaoConfig()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return ImportacaoConfig.model_validate(data)
