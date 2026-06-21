"""Busca uma chave na aba SFT (col A = K&G&Q).

Uso:
  python scripts/lookup_chave_sft.py <planilha.xlsx> <chave>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from difal_importacao.reader import lookup_fornecedor_by_chave, read_auxiliar_sft  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    path = Path(sys.argv[1])
    chave = sys.argv[2].strip()
    if not path.exists():
        print(f"Arquivo não encontrado: {path}")
        return 1

    lookups = read_auxiliar_sft(path)
    print(f"Chaves indexadas na SFT: {len(lookups)}")

    hit = lookup_fornecedor_by_chave(lookups, chave)
    if hit:
        print(f"ENCONTRADA: {chave}")
        print(f"  Nome:    {hit.nome_fornecedor!r}")
        print(f"  Emissão: {hit.data_emissao}")
        print(f"  Entrada: {hit.data_entrada}")
        return 0

    print(f"NÃO ENCONTRADA: {chave}")
    # amostra de chaves parecidas (prefixo)
    prefix = chave[:12]
    similares = [k for k in lookups if k.startswith(prefix)][:5]
    if similares:
        print(f"Chaves com prefixo {prefix!r}:")
        for k in similares:
            print(f"  {k}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
