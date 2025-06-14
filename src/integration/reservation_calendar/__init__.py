from httpx import AsyncClient
from misho.sportbooking.domain.session_token import SessionToken
from misho.sportbooking.domain.reservation_calendar import UserReservationCalendar
from misho.sportbooking.integration.reservation_calendar.reservation_calendar import get_reservation_calendar as get_reservation_calendar_api


async def get_reservation_calendar(http_client: AsyncClient, token: SessionToken) -> UserReservationCalendar:
    return await get_reservation_calendar_api(http_client, token)
