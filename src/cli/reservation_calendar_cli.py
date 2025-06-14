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
from misho.api.reservation_calendar import DayReservation
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

    for date, calendar in calendar.items():
        rendered = format_calendar_for_day(date, calendar)
        typer.echo(rendered)


def format_calendar_for_day(date: datetime.date, calendar: DayReservation) -> str:
    day_of_week = date.strftime("%A")
    table = Table(
        title=f"Reservation Calendar - {day_of_week} {date.strftime("%d.%m.%Y")}", show_lines=True)

    courts = [court_info.court_id for court_info in calendar.slots[0].courts]

    table.add_column("Time")
    for court in courts:
        table.add_column(f"Court {court}", justify="center")

    for slot in calendar.slots:
        hour = f'{slot.hour_slot.from_hour}:00 - {slot.hour_slot.to_hour}:00'
        courts = slot.courts

        columns = [
            hour] + [slot_name_styled(court.reserved_by, court.reserved_by_user) for court in courts]
        table.add_row(*columns)

    with console.capture() as capture:
        console.print(table)
    return capture.get()


def slot_name_styled(reserved_by: str | None, reserved_by_user: bool) -> str:
    if reserved_by is None:
        return "[dim]Available[/dim]"
    elif reserved_by_user:
        return f"[green]{reserved_by}[/green]"
    else:
        return f"[red]{reserved_by}[/red]"


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
