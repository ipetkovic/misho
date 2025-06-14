import asyncio
import datetime
from enum import Enum
from click import Parameter
import typer
import typer.utils

from cli.common import HTTP_CLIENT, get_authorization, get_default_courts_by_priority
from cli.date_or_weekday import parse_date_or_weekday
from misho.api import Error, NotFound
from misho.api.job import Job, JobCreate
from misho.api.reservation_calendar import Slot
from misho.client.job_client import JobClient
from misho.client.reservation_calendar_client import ReservationCalendarClient
from misho.domain.hour_slot import HourSlot
from misho.domain.job import Status

from rich.table import Table
from rich.console import Console

from misho.domain.monitoring_job import MonitoringAction, MonitoringJobCreate
from misho.domain.time_slot import TimeSlot

console = Console()


calendar_app = typer.Typer(help="Commands related to reservation calendar")
calendar_client = ReservationCalendarClient(http_client=HTTP_CLIENT,
                                            base_url="http://localhost:8000")


@calendar_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@calendar_app.command(
    "get",
    help="Get the reservation calendar"
)
def get_calendar(
    day: str = typer.Option(None,
                            help="Date for the job in DD.MM.YYYY format or weekday name (e.g. Monday)"),
):
    date = None
    if day:
        date = parse_date_or_weekday(day)

    calendar = asyncio.run(
        calendar_client.get_calendar(authorization=get_authorization())
    ).calendar

    if date is not None:
        if date not in calendar:
            typer.echo(f"No reservations found for {date}.")
            raise typer.Exit()

        calendar = {date: calendar[date]}

    typer.echo(calendar)


def format_jobs_table(calendar: dict[datetime.date, list[Slot]]) -> str:
    table = Table(title="Reservation Calendar", show_lines=True)

    courts = {slot.court_id for slots in calendar.values() for slot in slots}

    table.add_column("Time")
    # table.add_column("Date")
    # table.add_column("Day")
    # table.add_column("Time Slot")

    for court in courts:
        table.add_column(f"Court {court}", justify="center")

    for date, slots in calendar.items():

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
