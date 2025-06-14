import httpx

from misho.client import Authorization


HTTP_CLIENT = httpx.AsyncClient(
    base_url="localhost:8000", timeout=httpx.Timeout(10.0, connect=5.0))


def get_authorization() -> Authorization:
    return Authorization(token="4a7b99400983d2067a7c54f8d3cf7274")
