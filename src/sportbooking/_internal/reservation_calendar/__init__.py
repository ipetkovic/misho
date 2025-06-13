import datetime
from httpx import AsyncClient
import pydantic

from sportbooking.reservation_calendar import UserReservationCalendar
from sportbooking._internal.reservation_calendar.reservation_calendar import get_reservation_calendar as get_reservation_calendar_api


class HourSlot(pydantic.BaseModel):
    from_hour: int
    to_hour: int

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class TimeSlot(pydantic.BaseModel):
    date: datetime.date
    hour_slot: HourSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


async def get_reservation_calendar(http_client: AsyncClient, token: str) -> UserReservationCalendar:
    return await get_reservation_calendar_api(http_client, token)
