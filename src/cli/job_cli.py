import asyncio
import datetime
from enum import Enum
from click import Parameter
import typer
import typer.utils

from cli.common import HTTP_CLIENT, get_authorization, get_default_courts_by_priority
from misho.api import Error
from misho.api.job import Job, JobCreate
from misho.client.job_client import JobClient
from misho.domain.hour_slot import HourSlot
from misho.domain.job import Status

from rich.table import Table
from rich.console import Console

from misho.domain.monitoring_job import MonitoringAction, MonitoringJobCreate
from misho.domain.time_slot import TimeSlot

console = Console()


job_app = typer.Typer(help="Commands related to jobs")
job_client = JobClient(http_client=HTTP_CLIENT,
                       base_url="http://localhost:8000")


@job_app.command("list")
def list_jobs(
    status: Status = typer.Option(None, help="Filter jobs by status")
):
    jobs = asyncio.run(
        job_client.list_jobs(authorization=get_authorization(), status=status)
    )
    # print(f"Retrieved {len(jobs)} jobs")
    rendered = format_jobs_table(jobs)
    typer.echo(rendered)


def parse_date(date_str: str) -> datetime.date:
    pass


class Action(Enum):
    RESERVE = "reserve"
    NOTIFY = "notify"


@job_app.command("create")
def create_job(
    day: str = typer.Argument(...,
                              help="Date for the job in DD.MM.YYYY format or weekday name (e.g. Monday)"),
    hour_slot: tuple[int, int] = typer.Argument(
        ...,  help="From hour and to hour"),

    action: Action = typer.Argument(
        ..., help="Either 'reserve' or 'notify'"),
    courts: list[int] = typer.Option(
        get_default_courts_by_priority(),
        "-c", "--courts",
        help=f"List of court IDs by priority to reserve. Default: {get_default_courts_by_priority()}",
    ),
):
    date = parse_date_or_weekday(day)

    match action:
        case Action.RESERVE:
            monitoring_action = MonitoringAction.RESERVE
        case Action.NOTIFY:
            monitoring_action = MonitoringAction.NOTIFY

    job_create = JobCreate(
        time_slot=TimeSlot(
            date=date,
            hour_slot=HourSlot(from_hour=hour_slot[0], to_hour=hour_slot[1])
        ),
        job_type=MonitoringJobCreate(action=monitoring_action),
        courts_by_priority=courts
    )

    job_or_error = asyncio.run(
        job_client.create_job(
            authorization=get_authorization(), job_create=job_create)
    )

    if isinstance(job_or_error, Error):
        error = job_or_error
        typer.secho(error.root.error, fg=typer.colors.RED)
        typer.secho("Job creation failed", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

    job = job_or_error
    typer.secho("Job creation succeeded", fg=typer.colors.GREEN, bold=True)
    typer.echo(format_jobs_table([job]))


@job_app.command("delete")
def delete_job(
    job_id: int = typer.Argument(..., help="ID of the job to delete")
):

    job_found = asyncio.run(
        _delete_job(job_id=job_id)
    )

    if not job_found:
        typer.echo(f"Job with ID {job_id} not found.")
        raise typer.Exit(code=1)

    typer.echo(f"Job with ID {job_id} successfully deleted.")


async def _delete_job(job_id: int) -> bool:
    job = await job_client.get_job(authorization=get_authorization(), job_id=job_id)

    if job is None:
        return False

    await job_client.delete_job(authorization=get_authorization(), job_id=job_id)
    return True

WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6
}


def parse_date_or_weekday(value: str) -> datetime.date:
    # Try parse as date DD.MM.YYYY
    try:
        return datetime.datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        pass

    # Try parse as weekday
    weekday = value.strip().lower()
    if weekday not in WEEKDAYS:
        raise typer.BadParameter(
            f"Must be a date DD.MM.YYYY or weekday name (e.g. Monday), got '{value}'"
        )

    today = datetime.date.today()
    target_weekday = WEEKDAYS[weekday]
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:  # Target day already passed this week, get next week's
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def render_job(job):
    typer.echo(f"Job ID: {job.id}, Name: {job.name}, Status: {job.status}")


def format_jobs_table(jobs: list[Job]) -> str:
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
            str(job.job_type.action.name),
            created_at_str,
            status_styled(job.status),
        )
    # Render table to string
    with console.capture() as capture:
        console.print(table)
    return capture.get()


def status_styled(status: Status) -> str:
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
