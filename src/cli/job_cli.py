import asyncio
import typer

from cli.common import HTTP_CLIENT, get_authorization
from misho.client.job_client import JobClient
from misho.domain.job import Status

job_app = typer.Typer(help="Commands related to jobs")
job_client = JobClient(http_client=HTTP_CLIENT)


@job_app.command("list")
def list_jobs(
    status: Status = typer.Option(None, help="Filter jobs by status")
):
    jobs = asyncio.run(
        job_client.list_jobs(authorization=get_authorization(), status=status)
    )
    typer.echo(jobs)


@job_app.command("create")
def create_job(name: str):
    typer.echo(f"Creating job with name: {name}")
