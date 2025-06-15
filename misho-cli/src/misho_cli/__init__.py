import typer
from misho_cli.config import CONFIG
from misho_cli.job_cli import job_app
from misho_cli.reservation_calendar_cli import calendar_app

app = typer.Typer(help="Misho CLI")

# create typer with description
app = typer.Typer(
    help="Misho CLI - Command Line Interface for Misho - Sportbooking reservation management system",
)

app.add_typer(job_app, name="job")
app.add_typer(calendar_app, name="calendar")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if CONFIG.token is None:
        typer.echo(
            "❌ Access key is not defined. You can define it by setting MISHO_ACCESS_KEY environment variable", err=True)
        raise typer.Exit(code=1)

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main():
    app()
