"""CLI — Interface de linha de comando para o Motor de Oferta v0."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from models.motor_oferta import gerar_oferta, buscar_precatorios

app = typer.Typer(help="Motor de Oferta Indicativa de Precatórios Federais v0")
console = Console()


@app.command()
def oferta(
    cnj: str = typer.Argument(help="Número CNJ ou chave SOF do precatório"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output em JSON"),
):
    """Gera oferta indicativa para um precatório dado seu número CNJ."""
    resultado = gerar_oferta(numero_cnj=cnj)

    if resultado is None:
        console.print(f"[red]✗ Precatório '{cnj}' não encontrado na base.[/red]")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps(resultado.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_oferta(resultado)


@app.command()
def oferta_manual(
    tribunal: str = typer.Option(..., "--tribunal", "-t", help="Tribunal (ex: TRF4)"),
    natureza: str = typer.Option(..., "--natureza", "-n", help="Natureza (ex: PREVIDÊNCIA)"),
    exercicio: int = typer.Option(..., "--exercicio", "-e", help="Exercício orçamentário"),
    valor: float = typer.Option(..., "--valor", "-v", help="Valor nominal (R$)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output em JSON"),
):
    """Gera oferta indicativa com parâmetros manuais (sem busca no banco)."""
    resultado = gerar_oferta(
        tribunal=tribunal,
        natureza=natureza,
        exercicio=exercicio,
        valor=valor,
    )

    if resultado is None:
        console.print("[red]✗ Não foi possível gerar oferta com os parâmetros fornecidos.[/red]")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps(resultado.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_oferta(resultado)


@app.command()
def buscar(
    tribunal: str = typer.Option(None, "--tribunal", "-t"),
    natureza: str = typer.Option(None, "--natureza", "-n"),
    exercicio: int = typer.Option(None, "--exercicio", "-e"),
    limit: int = typer.Option(10, "--limit", "-l"),
):
    """Busca precatórios no banco gold com filtros opcionais."""
    results = buscar_precatorios(tribunal=tribunal, natureza=natureza,
                                 exercicio=exercicio, limit=limit)

    if not results:
        console.print("[yellow]Nenhum precatório encontrado com os filtros informados.[/yellow]")
        return

    table = Table(title=f"Precatórios ({len(results)} resultados)")
    table.add_column("CNJ/Chave", style="cyan")
    table.add_column("Tribunal")
    table.add_column("Natureza")
    table.add_column("Exercício")
    table.add_column("Valor Nominal", justify="right", style="green")

    for r in results:
        table.add_row(
            str(r["numero_cnj"]),
            r["tribunal"],
            r["natureza"],
            str(r["exercicio"]),
            f"R$ {r['valor_nominal']:,.2f}" if r["valor_nominal"] else "-",
        )

    console.print(table)


@app.command()
def stats():
    """Mostra estatísticas do banco gold."""
    from db import get_connection
    con = get_connection()

    total = con.execute("SELECT COUNT(*) FROM gold.precatorios").fetchone()[0]
    valor_total = con.execute("SELECT SUM(valor_nominal) FROM gold.precatorios").fetchone()[0]

    console.print(Panel(
        f"[bold]Banco Gold[/bold]\n"
        f"Total de precatórios: {total:,}\n"
        f"Valor nominal total: R$ {valor_total:,.2f}\n"
        f"Valor médio: R$ {valor_total/total:,.2f}" if total > 0 else "Banco vazio",
        title="📊 Estatísticas",
    ))

    # Top tribunais
    dist = con.execute("""
        SELECT tribunal, COUNT(*) as qtd, ROUND(SUM(valor_nominal),2) as total
        FROM gold.precatorios GROUP BY tribunal ORDER BY qtd DESC LIMIT 5
    """).fetchall()

    table = Table(title="Top Tribunais")
    table.add_column("Tribunal")
    table.add_column("Quantidade", justify="right")
    table.add_column("Valor Total", justify="right")

    for row in dist:
        table.add_row(row[0], f"{row[1]:,}", f"R$ {row[2]:,.0f}")

    console.print(table)
    con.close()


def _print_oferta(oferta):
    """Imprime oferta formatada no terminal."""
    console.print(Panel(
        f"[bold cyan]Precatório:[/bold cyan] {oferta.numero_cnj}\n"
        f"[bold]Tribunal:[/bold] {oferta.tribunal}\n"
        f"[bold]Natureza:[/bold] {oferta.natureza}\n"
        f"[bold]Exercício:[/bold] {oferta.exercicio}\n"
        f"[bold]Duration estimada:[/bold] {oferta.duration_estimada} anos\n"
        f"\n"
        f"[bold]Valor Nominal:[/bold] R$ {oferta.valor_nominal:,.2f}\n"
        f"[bold green]Faixa de Oferta:[/bold green] "
        f"R$ {oferta.valor_oferta_min:,.2f} — R$ {oferta.valor_oferta_max:,.2f}\n"
        f"[dim]Deságio: {oferta.desagio_min*100:.1f}% — {oferta.desagio_max*100:.1f}%[/dim]\n"
        f"\n"
        f"[dim italic]{oferta.disclaimer}[/dim italic]",
        title="💰 Oferta Indicativa",
        border_style="green",
    ))

    # Premissas
    table = Table(title="Premissas do Cálculo")
    table.add_column("Parâmetro")
    table.add_column("Valor")

    for k, v in oferta.premissas.items():
        table.add_row(k, str(v))

    console.print(table)


if __name__ == "__main__":
    app()
