from urllib.parse import urlencode
from httpx import AsyncClient, Request
import httpx

from sportbooking._internal.common import HOST, get_standard_headers

URL = HOST + '/main/rezervacijaterena.php'


async def reserve(http_client: AsyncClient, token: str, reservation_input: dict[str, str]) -> None:
    response = await http_client.send(_request(token, reservation_input))
    return _parse_response(response)


def _request(token: str, reservation_input: dict[str, str]) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token
    headers['Referer'] = HOST + '/main/cland.php'
    headers['Sec-Fetch-Mode'] = 'navigate'
    headers['Sec-Fetch-Site'] = 'same-origin'
    headers['Sec-Fetch-User'] = '?1'
    headers['Sec-Ch-Ua-Platform'] = 'macOS'
    headers['Sec-Ch-Ua-Mobile'] = '?0'
    headers['Cache-Control'] = 'no-cache'
    headers['Pragma'] = 'no-cache'
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers['upgrade-insecure-requests'] = '1'
    payload = urlencode(reservation_input)

    return Request(
        method='POST',
        url=URL,
        headers=headers,
        data=payload
    )


def _parse_response(response: httpx.Response):
    if response.status_code != 200:
        raise Exception(
            f"Failed to reserve: {response.status_code}")

    # TODO - verify if ok
