"""Recursos visuais compartilhados (logo) — dev e executável PyInstaller."""
from __future__ import annotations

import sys
from pathlib import Path


def _bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2]


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def logo_path() -> Path | None:
    bundle = _bundle_root()
    app = _app_root()
    candidates = (
        bundle / "assets" / "logo_madero.jpeg",
        app / "logo_madero.jpeg",
        app / "logo_madero.jpg",
        app / "assets" / "logo_madero.jpeg",
        app / "assets" / "logo_madero.jpg",
        bundle / "logo_madero.jpeg",
    )
    for path in candidates:
        if path.exists():
            return path
    return None
