import typer
from cli.job_cli import job_app
from cli.reservation_calendar_cli import calendar_app

app = typer.Typer(help="Misho CLI")

# create typer with description
app = typer.Typer(
    help="Misho CLI - Command Line Interface for Misho - Sportbooking reservation management system",
)

app.add_typer(job_app, name="job")
app.add_typer(calendar_app, name="calendar")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
