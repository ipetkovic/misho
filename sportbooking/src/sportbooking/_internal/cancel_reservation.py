from urllib.parse import urlencode
from httpx import AsyncClient, Request
import httpx

from sportbooking._internal.common import HOST, get_standard_headers

URL = HOST + '/main/otkazivanjerezervacije.php'


async def cancel_reservation(http_client: AsyncClient, token: str, cancellation_input: dict[str, str]) -> None:
    response = await http_client.send(_request(token, cancellation_input))
    return _parse_response(response)


def _request(token: str, cancellation_input: dict[str, str]) -> Request:
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
    payload = urlencode(cancellation_input)

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


if __name__ == "__main__":
    import asyncio

    async def main():
        async with AsyncClient() as client:
            cancellation_input = {'idbroj': '151962', 'danre': '15.07.2025', 'rteren': '7',
                                  'termin': '07:00-08:00', 'submit': 'Otkaži rezervaciju', 'razod': '6'}
            await cancel_reservation(
                http_client=client,
                token='PHPSESSID=6fba6b039a91654509cbf43010cf16ae',
                cancellation_input=cancellation_input
            )

    asyncio.run(main())
