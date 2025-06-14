import typer
from cli.job_cli import job_app

app = typer.Typer(help="Misho CLI")

app.add_typer(job_app, name="jobs")

if __name__ == "__main__":
    app()
