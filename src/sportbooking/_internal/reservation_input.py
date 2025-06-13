from bs4 import BeautifulSoup
from httpx import AsyncClient, Request, Response

from sportbooking._internal.common import HOST, get_standard_headers
from sportbooking.reservation_query_input import ReservationQueryInput

URL = HOST + '/main/'


async def get_reservation_query_input(http_client: AsyncClient, token: str, reservation_url: str) -> ReservationQueryInput:
    response = await http_client.send(_request(token, reservation_url))
    return _parse_response(response)


def _request(token: str, reservation_url: str) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token
    headers['Referer'] = HOST + '/main/cland.php'
    headers['Sec-Fetch-Mode'] = 'navigate'
    headers['Sec-Fetch-Site'] = 'none'

    return Request(
        method='GET',
        url=URL + reservation_url,
        headers=headers
    )


def _parse_response(response: Response) -> ReservationQueryInput:
    if response.status_code != 200:
        raise Exception(
            f"Failed to get reservation data: {response.status_code}")

    return _parse_reservation_input(response.text)


def _parse_reservation_input(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find_all("div", class_="rezervacijaterenapanel")[0]

    input_fields = (
        'rsatni', 'lmter1', 'terpi', 'brojk', 'danre', 'rteren', 'termin', 'cijena', 'protiv', 'submit'
    )

    reservation_input = {name: div.find('input', attrs={'name': name}).get(
        'value') for name in input_fields}

    return reservation_input
