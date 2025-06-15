import datetime
from enum import Enum
import typer

from misho_cli.common import get_authorization, get_default_courts_by_priority, misho_base_url
from misho_cli.config import CONFIG
from misho_cli.date_or_weekday import parse_date_or_weekday
from misho_cli.reserve_id import ReserveId
from misho_api import Error, NotFound
from misho_api.hour_slot import HourSlotApi
from misho_api.job import ActionApi, JobApi, JobCreateApi, StatusApi
from rich.table import Table
from rich.console import Console
from misho_api.time_slot import TimeSlotApi
from misho_client.job_client import JobClient

console = Console()


job_app = typer.Typer(help="Commands related to jobs")
job_client = JobClient(base_url=misho_base_url())


@job_app.command(
    "list",
    help="List all jobs with optional filtering by status"
)
def list_jobs(
    status: StatusApi = typer.Option(None, help="Filter jobs by status")
):
    jobs = job_client.list_jobs(
        authorization=get_authorization(), status=status)
    rendered = format_jobs_table(jobs)
    typer.echo(rendered)


@job_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def parse_date(date_str: str) -> datetime.date:
    pass


class Action(Enum):
    RESERVE = "reserve"
    NOTIFY = "notify"


@job_app.command(
    "create",
    help="Create a new job to reserve when slot becomes available or notify about reservations",
)
def create_job(
    day: str = typer.Option(None, "-d", "--day",
                            help="Date for the job in DD.MM.YYYY format or weekday name (e.g. Monday). Must be provided together with hour option."),
    hour: tuple[int, int] = typer.Option(None, "-h", "--hour",
                                         help="Start and end hour of the time slot, e.g. '10 11' for 10:00-11:00. Must be provided together with day option."),
    link: str = typer.Option(
        None, "-l", "--link",
        help="Reservation slot link. If provided, day and hour options are ignored."),
    action: Action = typer.Argument(
        ..., help="Either 'reserve' or 'notify'"),
    courts: list[int] = typer.Option(
        get_default_courts_by_priority(),
        "-c", "--courts",
        help=f"List of court IDs by priority to reserve. Default: {get_default_courts_by_priority()}",
    ),
):
    if link is not None:
        time_slot = ReserveId(id=link).to_time_slot()
        date = time_slot.date
        from_hour = time_slot.hour_slot.from_hour
        to_hour = time_slot.hour_slot.to_hour
    else:

        if day is None or hour is None:
            typer.secho(
                "Both day and hour options must be provided together, or use link", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        date = parse_date_or_weekday(day)
        from_hour, to_hour = hour

    match action:
        case Action.RESERVE:
            job_action = ActionApi.RESERVE
        case Action.NOTIFY:
            job_action = ActionApi.NOTIFY

    job_create = JobCreateApi(
        time_slot=TimeSlotApi(
            date=date,
            hour_slot=HourSlotApi(from_hour=from_hour, to_hour=to_hour)
        ),
        action=job_action,
        courts_by_priority=courts
    )

    job_or_error = job_client.create_job(
        authorization=get_authorization(), job_create=job_create)

    if isinstance(job_or_error, Error):
        error = job_or_error
        typer.secho(error.root.error, fg=typer.colors.RED)
        typer.secho("Job creation failed", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

    job = job_or_error
    typer.secho("Job creation succeeded", fg=typer.colors.GREEN, bold=True)
    typer.echo(format_jobs_table([job]))


@job_app.command(
    "delete",
    help="Delete a job by its ID"
)
def delete_job(
    job_id: int = typer.Argument(..., help="ID of the job to delete")
):
    job_or_error = job_client.get_job(
        authorization=get_authorization(), job_id=job_id)

    if isinstance(job_or_error, Error):
        if isinstance(job_or_error.root, NotFound):
            typer.echo(f"Job with ID {job_id} not found.")
            raise typer.Exit(code=1)

    job_client.delete_job(authorization=get_authorization(), job_id=job_id)
    typer.echo(f"Job with ID {job_id} successfully deleted.")


def format_jobs_table(jobs: list[JobApi]) -> str:
    table = Table(title="Jobs List")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Date")
    table.add_column("Day")
    table.add_column("Time Slot")
    table.add_column("Courts")
    table.add_column("Action")
    table.add_column("Created At")
    table.add_column("Status")

    for job in jobs:
        courts_str = ", ".join(str(court) for court in job.courts_by_priority)
        created_at_str = job.created_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(
            str(job.id),
            str(job.time_slot.date),
            job.time_slot.date.strftime("%A"),
            str(job.time_slot.hour_slot),
            courts_str,
            str(job.action.name),
            created_at_str,
            status_styled(job.status),
        )
    # Render table to string
    with console.capture() as capture:
        console.print(table)
    return capture.get()


def status_styled(status: StatusApi) -> str:
    status_text = str(status.name)
    if status_text == "FAILED":
        status_styled = f"[red]{status_text}[/red]"
    elif status_text == "PENDING":
        status_styled = f"[yellow]{status_text}[/yellow]"
    elif status_text == "SUCCESS":
        status_styled = f"[green]{status_text}[/green]"
    else:
        status_styled = status_text

    return status_styled
