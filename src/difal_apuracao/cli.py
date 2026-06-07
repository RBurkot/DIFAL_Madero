from pathlib import Path

import typer

from difal_apuracao.calculator import calcular_apuracao
from difal_apuracao.config import load_config
from difal_apuracao.reader import read_bi, validate_bi_layout
from difal_apuracao.writer import write_difal_sheet

app = typer.Typer(help="Apuração DIFAL Indústria a partir do extrato BI")


@app.command("gerar")
def gerar(
    entrada: Path = typer.Argument(..., help="Arquivo BI .xlsx"),
    periodo: str = typer.Option(..., "--periodo", "-p", help="Período MM.AAAA"),
    saida: Path | None = typer.Option(None, "--saida", "-o"),
    corte_dia: int | None = typer.Option(None, "--corte-dia"),
    config: Path | None = typer.Option(None, "--config", "-c"),
):
    """Gera aba DIFAL a partir do extrato BI."""
    valid, errors = validate_bi_layout(entrada)
    if not valid:
        for e in errors:
            typer.echo(f"ERRO: {e}", err=True)
        raise typer.Exit(1)

    mes, ano = periodo.replace("/", ".").split(".")
    cfg = load_config(config)
    linhas_bi = read_bi(entrada, int(mes), int(ano), corte_dia)
    if not linhas_bi:
        typer.echo("AVISO: Nenhuma linha encontrada para o período informado.", err=True)
        raise typer.Exit(1)

    linhas_difal = calcular_apuracao(linhas_bi, cfg)
    out = saida or entrada.parent / f"apuracao-difal-{periodo.replace('/', '')}.xlsx"
    write_difal_sheet(linhas_difal, out, periodo.replace("/", "."))
    typer.echo(f"Período: {periodo}")
    typer.echo(f"Linhas apuradas: {len(linhas_difal)}")
    typer.echo(f"Saída: {out}")


if __name__ == "__main__":
    app()
