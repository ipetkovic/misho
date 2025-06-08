from bs4 import BeautifulSoup
from httpx import AsyncClient, Request, Response
import core.sportbooking.integration.reservation_input as reservation_input
from core.sportbooking.domain.session_token import SessionToken
from core.sportbooking.integration.common import *

URL = HOST + '/main/'


type ReservationQueryInput = dict[str, str]


async def get_reservation_query_input(http_client: AsyncClient, token: SessionToken, reservation_url: str) -> ReservationQueryInput:
    response = await http_client.send(_request(token, reservation_url))
    return _parse_response(response)


def _request(token: SessionToken, reservation_url: str) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token.value
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


# if __name__ == "__main__":
#     token = SessionToken(value='PHPSESSID=53cde7d998502faaaffb4236320159c7')
#     reservation_input = reservation_input.get_reservation_query_input(
#         token, 'rezervacijaterena.php?bqw765t3r=762614492723484fa53be91b4933d536748a60458b9797')

#     print(reservation_input)
