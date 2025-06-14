import asyncio
import datetime
from enum import Enum
from click import Parameter
import typer
import typer.utils

from cli.common import HTTP_CLIENT, get_authorization, get_default_courts_by_priority
from misho.api import Error, NotFound
from misho.api.job import Job, JobCreate
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
    status: Status = typer.Option(None, help="Filter jobs by status")
):
    jobs = asyncio.run(
        calendar_client.get_calendar(authorization=get_authorization())
    )
    typer.echo(jobs)
