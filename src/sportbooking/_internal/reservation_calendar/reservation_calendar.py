from httpx import AsyncClient, Request
from sportbooking._internal.common import HOST, get_standard_headers
from sportbooking._internal.reservation_calendar import reservation_calendar_html_parser
from sportbooking.reservation_calendar import UserReservationCalendar


URL = HOST + '/main/cland.php'


async def get_reservation_calendar(client: AsyncClient, token: str) -> UserReservationCalendar:
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


def _request(token: str) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token
    headers['Referer'] = HOST + '/index.php'

    return Request(
        method='GET',
        url=URL,
        headers=headers
    )
