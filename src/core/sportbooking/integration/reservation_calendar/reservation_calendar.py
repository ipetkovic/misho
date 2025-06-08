import asyncio
from dataclasses import dataclass
from httpx import AsyncClient, Request
from core.sportbooking.domain.session_token import SessionToken
from core.sportbooking.integration.common import *
from core.sportbooking.integration.reservation_calendar import reservation_calendar_html_parser
from core.sportbooking.domain.reservation_calendar import UserReservationCalendar


URL = HOST + '/main/cland.php'


async def get_reservation_calendar(client: AsyncClient, token: SessionToken) -> UserReservationCalendar:
    """
    List all reservations for the user associated with the session token.
    """

    async def send():
        return await client.send(_request(token))

    response = await send()

    if response.status_code != 200:
        raise Exception(
            f"Failed to list reservations: {response.status_code}")

    invalid_response_content = "window.location.replace('logout.php')"

    if invalid_response_content in response.text[:1000]:
        raise Exception("Cannot get reservation calendar")

    return reservation_calendar_html_parser.parse(response.text)


def _request(token: SessionToken) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token.value
    headers['Referer'] = HOST + '/index.php'

    return Request(
        method='GET',
        url=URL,
        headers=headers
    )
