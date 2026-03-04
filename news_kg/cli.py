"""CLI entry point for news-kg."""

import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo("news-kg")


if __name__ == "__main__":
    app()
