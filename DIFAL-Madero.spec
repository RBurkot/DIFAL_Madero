# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — executável desktop DIFAL Madero."""
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ["src/difal_desktop/__main__.py"],
    pathex=[str(root / "src")],
    binaries=[],
    datas=[
        (str(root / "config"), "config"),
        (str(root / "logo_madero.jpeg"), "assets"),
    ],
    hiddenimports=[
        "openpyxl",
        "openpyxl.cell._writer",
        "PIL",
        "yaml",
        "pydantic",
        "typer",
        "difal_apuracao",
        "difal_importacao",
        "difal_api",
        "difal_api.orchestrator",
        "difal_api.job_store",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "fastapi",
        "uvicorn",
        "starlette",
        "httpx",
        "sse_starlette",
        "multipart",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DIFAL-Madero",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
