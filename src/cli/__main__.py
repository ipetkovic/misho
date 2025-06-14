import typer
from cli.job_cli import job_app

app = typer.Typer(help="Misho CLI")

# create typer with description
app = typer.Typer(
    help="Misho CLI - Command Line Interface for Misho - Sportbooking reservation management system",
    no_args_is_help=True,
)

app.add_typer(job_app, name="job")

if __name__ == "__main__":
    app()
