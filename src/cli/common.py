import httpx

from misho.client import Authorization


HTTP_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0, connect=5.0))


def get_authorization() -> Authorization:
    return Authorization(token="4a7b99400983d2067a7c54f8d3cf7274")


def get_default_courts_by_priority() -> list[int]:
    """
    Returns a list of default courts by priority.
    """
    return [4, 6, 5, 7]
