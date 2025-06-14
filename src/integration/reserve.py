from urllib.parse import urlencode
from httpx import AsyncClient, Request
import requests
import misho.sportbooking.integration.reservation_input as reservation_input
from misho.sportbooking.domain.session_token import SessionToken
from misho.sportbooking.integration.common import get_standard_headers, HOST

URL = HOST + '/main/rezervacijaterena.php'


async def reserve(http_client: AsyncClient, token: SessionToken, reservation_input: dict[str, str]) -> None:
    response = await http_client.send(_request(token, reservation_input))
    return _parse_response(response)


def _request(token: SessionToken, reservation_input: dict[str, str]) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token.value
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


def _parse_response(response: requests.Response):
    if response.status_code != 200:
        raise Exception(
            f"Failed to reserve: {response.status_code}")

    # TODO - verify if ok


# if __name__ == "__main__":
#     token = SessionToken(value='PHPSESSID=53cde7d998502faaaffb4236320159c7')
#     input = {'rsatni': '11', 'lmter1': '', 'terpi': '0', 'brojk': '562614a92723484fa53be91ba933d536748a60458b9797',
#              'danre': '04.06.2025', 'rteren': '6', 'termin': '17:00-19:00', 'cijena': '0', 'protiv': '', 'submit': 'Rezerviraj teren'}
#     reserve(token, input)
