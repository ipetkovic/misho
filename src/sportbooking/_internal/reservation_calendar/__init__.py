import datetime
from httpx import AsyncClient
import pydantic

from sportbooking.reservation_calendar import UserReservationCalendar
from sportbooking._internal.reservation_calendar.reservation_calendar import get_reservation_calendar as get_reservation_calendar_api


async def get_reservation_calendar(http_client: AsyncClient, token: str) -> UserReservationCalendar:
    return await get_reservation_calendar_api(http_client, token)
