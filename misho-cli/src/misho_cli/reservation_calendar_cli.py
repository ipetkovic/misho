import datetime
import typer

from misho_cli.common import get_authorization, misho_base_url
from misho_cli.date_or_weekday import parse_date_or_weekday
from misho_cli.reserve_id import ReserveId
from misho_api import Error, NotFound
from misho_api.job import JobApi, JobCreateApi, StatusApi
from misho_api.reservation_calendar import CourtInfo, DayReservation

from rich.table import Table
from rich.console import Console

from misho_api.time_slot import TimeSlotApi
from misho_client.job_client import JobClient
from misho_client.reservation_calendar_client import ReservationCalendarClient

console = Console()
calendar_app = typer.Typer(help="Commands related to reservation calendar")

calendar_client = ReservationCalendarClient(base_url=misho_base_url())
job_client = JobClient(base_url=misho_base_url())


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
    day: str = typer.Option(None, "-d", "--day",
                            help="Date for the job in DD.MM.YYYY format or weekday name (e.g. Monday)"),
):
    date = None
    if day:
        date = parse_date_or_weekday(day)

    calendar = calendar_client.get_calendar(
        authorization=get_authorization()).calendar
    jobs = job_client.list_jobs(authorization=get_authorization())

    if date is not None:
        if date not in calendar:
            typer.echo(f"No reservations found for {date}.")
            raise typer.Exit()

        calendar = {date: calendar[date]}

    for date, calendar in calendar.items():
        rendered = format_calendar_for_day(date, calendar, jobs)
        typer.echo(rendered)


def format_calendar_for_day(date: datetime.date, calendar: DayReservation, jobs: list[JobApi]) -> str:
    day_of_week = date.strftime("%A")
    table = Table(
        title=f"Reservation Calendar - {day_of_week} {date.strftime("%d.%m.%Y")}", show_lines=True)

    courts = [court_info.court_id for court_info in calendar.slots[0].courts]

    table.add_column("Time", justify="right")
    for court in courts:
        table.add_column(f"Court {court}", justify="center")
    table.add_column("Link", justify="center")

    for slot in calendar.slots:
        job = next(
            (job for job in jobs if job.time_slot.date ==
             date and job.time_slot.hour_slot == slot.hour_slot),
            None  # default if not found
        )

        hour = f'{slot.hour_slot.from_hour}:00 - {slot.hour_slot.to_hour}:00'
        courts = slot.courts

        job_create_link = ReserveId.from_time_slot(
            TimeSlotApi(date=date, hour_slot=slot.hour_slot)
        )

        columns = [
            hour] + [slot_name_styled(job, court) for court in courts] + [job_create_link.id]
        table.add_row(*columns)

    with console.capture() as capture:
        console.print(table)
    return capture.get()


def job_render(job: JobApi | None, court_id: int) -> str:
    if job is None or court_id not in job.courts_by_priority:
        return ''
    return f'\n[yellow]{job.job_type.action.name} ({job.id})[/yellow]'


def slot_name_styled(job: JobApi | None, court: CourtInfo) -> str:
    if court.reserved_by is None:
        return "[dim]Available[/dim]" + job_render(job, court.court_id)
    elif court.reserved_by_user:
        return f"[green]{court.reserved_by}[/green]" + job_render(job, court.court_id)
    else:
        return f"[red]{court.reserved_by}[/red]" + job_render(job, court.court_id)


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
