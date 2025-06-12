

from bs4 import BeautifulSoup
from httpx import AsyncClient, Request, Response
import pydantic

from core.sportbooking.domain.session_token import SessionToken
from core.sportbooking.integration.common import HOST, get_standard_headers


class UserAccountInfo(pydantic.BaseModel):
    name: str


URL = HOST + "/main/korisnickiracun.php"


async def get_account_info(http_client: AsyncClient, token: SessionToken) -> UserAccountInfo:
    response = await http_client.send(_request(token))
    return _parse_response(response)


def _request(token: SessionToken) -> Request:
    headers = get_standard_headers()
    headers['Cookie'] = token.value
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
    div = soup.find_next("div", class_="osobnipodaciimeiprezimefont1")

    if not div:
        raise Exception("Failed to parse account info")

    return UserAccountInfo(div.text.strip())
