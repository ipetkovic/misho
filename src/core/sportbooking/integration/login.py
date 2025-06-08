from dataclasses import dataclass
from urllib.parse import urlencode
from httpx import Request, AsyncClient, Response

from core.sportbooking.domain.session_token import SessionToken
from core.sportbooking.integration.common import *

URL = HOST + "/index.php"


@dataclass
class LoginResponse:
    token: SessionToken


async def login(client: AsyncClient, username: str, password: str) -> LoginResponse:
    """
    Login to the Sportbooking API and return the session token.
    """
    request = _request(username, password)
    response = await client.send(request)
    parsed = _parse_response(response)
    return parsed


def _request(username: str, password: str) -> Request:
    payload = urlencode(
        {"korime": username, "korloz": password, "submit": "Login"})

    headers = get_standard_headers()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    headers["Referer"] = URL

    return Request(
        method="POST",
        url=URL,
        data=payload,
        headers=headers
    )


def _parse_response(response: Response) -> LoginResponse:

    if response.status_code != 200:
        raise Exception(
            f"Login failed with status code {response.status_code}")

    must_contain = "window.location.replace('main/clan.php')"

    if must_contain not in response.text[:1000]:
        raise Exception("Login failed")

    token = response.headers['Set-Cookie'].split(';')[0]
    return LoginResponse(token=SessionToken(value=token))


if __name__ == "__main__":
    print(login("Ivo Petkovic", "i2802989"))
