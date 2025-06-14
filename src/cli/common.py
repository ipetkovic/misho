import httpx

from cli.config import CONFIG
from misho.client import Authorization


HTTP_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0, connect=5.0))


def get_authorization() -> Authorization:
    return Authorization(token=CONFIG.token)


def misho_base_url() -> str:
    """
    Returns the base URL for the Misho API.
    """
    return CONFIG.host_url + ":" + str(CONFIG.host_port)


def get_default_courts_by_priority() -> list[int]:
    """
    Returns a list of default courts by priority.
    """
    return [4, 6, 5, 7]
