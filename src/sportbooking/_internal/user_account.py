from bs4 import BeautifulSoup
from httpx import AsyncClient, Request, Response

from sportbooking._internal.common import HOST, get_standard_headers
from sportbooking.user_account_info import UserAccountInfo


URL = HOST + "/main/korisnickiracun.php"


async def get_account_info(http_client: AsyncClient, token: str) -> UserAccountInfo:
    response = await http_client.send(_request(token))
    return _parse_response(response)


def _request(token: str) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token
    headers['Referer'] = HOST + '/main/cland.php'
    headers['Sec-Fetch-Mode'] = 'navigate'
    headers['Sec-Fetch-Site'] = 'none'

    return Request(
        method='GET',
        url=URL,
        headers=headers
    )


def _parse_response(response: Response) -> UserAccountInfo:
    if response.status_code != 200:
        raise Exception(
            f"Failed to get account info: {response.status_code}")

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    name = soup.find("font", class_="osobnipodaciimeiprezimefont1")

    if not name:
        raise Exception("Failed to parse account info")

    name = name.text.strip()

    return UserAccountInfo(name=name)
