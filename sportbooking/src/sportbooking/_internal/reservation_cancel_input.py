from bs4 import BeautifulSoup
from httpx import AsyncClient, Request, Response

from sportbooking._internal.common import HOST, get_standard_headers
from sportbooking.reservation_query_input import ReservationQueryInput

URL = HOST + '/main/'


async def get_reservation_cancel_query_input(http_client: AsyncClient, token: str, cancellation_url: str) -> ReservationQueryInput:
    response = await http_client.send(_request(token, cancellation_url))
    return _parse_response(response)


def _request(token: str, cancellation_url: str) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token
    headers['Referer'] = HOST + '/main/cland.php'
    headers['Sec-Fetch-Mode'] = 'navigate'
    headers['Sec-Fetch-Site'] = 'none'

    return Request(
        method='GET',
        url=URL + cancellation_url,
        headers=headers
    )


def _parse_response(response: Response) -> ReservationQueryInput:
    if response.status_code != 200:
        raise Exception(
            f"Failed to get reservation data: {response.status_code}")

    return _parse_reservation_cancel_input(response.text)


def _parse_reservation_cancel_input(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.find_all("div", class_="rezervacijaterenapanel")[0]

    input_fields = (
        'idbroj', 'danre', 'rteren', 'termin', 'submit'
    )

    reservation_cancel_input: dict[str, str] = {name: div.find('input', attrs={'name': name}).get(  # type: ignore
        'value') for name in input_fields}

    reservation_cancel_input['razod'] = '6'

    return reservation_cancel_input


if __name__ == "__main__":
    import asyncio
    from httpx import AsyncClient

    async def main():
        async with AsyncClient() as client:
            result = await get_reservation_cancel_query_input(
                http_client=client,
                token='PHPSESSID=6fba6b039a91654509cbf43010cf16ae',
                cancellation_url='otkazivanjerezervacije.php?idbroj=151962'
            )


    asyncio.run(main())
