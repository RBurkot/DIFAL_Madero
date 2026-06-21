import json
from pathlib import Path

import typer

from difal_importacao.config import load_config
from difal_importacao.reader import load_sft_lookups, read_difal
from difal_importacao.reconciliation import reconciliar, save_relatorio
from difal_importacao.transformer import gerar_lancamentos
from difal_importacao.writer import write_importacao_sheet

app = typer.Typer(help="Geração INDUSTRIA-IMPORTAÇÃO a partir da aba DIFAL")


@app.command("gerar")
def gerar(
    entrada: Path = typer.Argument(..., help="Workbook com aba DIFAL"),
    saida: Path | None = typer.Option(None, "--saida", "-o"),
    aba_difal: str | None = typer.Option(None, "--aba-difal", "-d"),
    aba_auxiliar: str = typer.Option("SFT ", "--aba-auxiliar", "-a"),
    sem_enriquecimento: bool = typer.Option(False, "--sem-enriquecimento"),
    reconciliar_ref: Path | None = typer.Option(None, "--reconciliar", "-r"),
    relatorio: Path | None = typer.Option(None, "--relatorio"),
    config_path: Path | None = typer.Option(None, "--config", "-c"),
):
    cfg = load_config(config_path)
    periodo, linhas = read_difal(entrada, aba_difal)
    lookups: dict = {}
    if not sem_enriquecimento:
        lookups = load_sft_lookups(entrada, reconciliar_ref, aba_auxiliar)
    if reconciliar_ref:
        cfg = cfg.model_copy(update={"sb1_workbook": str(reconciliar_ref)})
    result = gerar_lancamentos(
        linhas, periodo, cfg, lookups,
        sb1_workbook=reconciliar_ref,
        entradas_workbook=reconciliar_ref or entrada,
    )

    out = saida or entrada.parent / f"importacao-{periodo.label.replace('.', '')}.xlsx"
    write_importacao_sheet(result.lancamentos, result.totais_difal, out, entrada)

    summary = {
        "periodo": periodo.label,
        "linhas_difal": len(linhas),
        "lancamentos_gerados": len(result.lancamentos),
        "excluidas_materialidade": result.excluidas_materialidade,
        "excecoes_conta": result.excecoes_conta,
        "saida": str(out),
    }
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))

    if reconciliar_ref:
        rel = reconciliar(out, reconciliar_ref, cfg, periodo.label)
        rel_path = relatorio or out.parent / "reconciliacao.json"
        save_relatorio(rel, rel_path)
        typer.echo(f"Reconciliação: {rel.resultado} → {rel_path}")


if __name__ == "__main__":
    app()
