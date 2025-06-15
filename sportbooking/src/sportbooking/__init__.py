import httpx
from sportbooking.login import LoginResponse
from sportbooking.reservation_calendar import UserReservationCalendar
from sportbooking.reservation_query_input import ReservationQueryInput
from sportbooking.user_account_info import UserAccountInfo
from sportbooking._internal.login import login as _login_api
from sportbooking._internal.reserve import reserve as _reserve_api
from sportbooking._internal.reservation_calendar import get_reservation_calendar as _get_reservation_calendar_api
from sportbooking._internal.user_account import get_account_info as _get_account_info_api
from sportbooking._internal.reservation_input import get_reservation_query_input as _get_reservation_query_input_api


class SportbookingApiInterface:
    async def login(self, username: str, password: str) -> LoginResponse:
        raise NotImplementedError()

    async def get_reservation_calendar(self, token: str) -> UserReservationCalendar:
        raise NotImplementedError()

    async def get_reservation_query_input(self, token: str, reservation_url: str) -> ReservationQueryInput:
        raise NotImplementedError()

    async def reserve(self, token: str, reservation_input: ReservationQueryInput) -> None:
        raise NotImplementedError()

    async def get_user_account_info(self, token: str) -> UserAccountInfo:
        raise NotImplementedError()


class SportbookingApi(SportbookingApiInterface):
    def __init__(self):
        self._http_client = httpx.AsyncClient()

    async def login(self, username: str, password: str) -> LoginResponse:
        return await _login_api(self._http_client, username, password)

    async def get_reservation_calendar(self, token: str) -> UserReservationCalendar:
        return await _get_reservation_calendar_api(self._http_client, token)

    async def get_reservation_query_input(self, token: str, reservation_url: str) -> ReservationQueryInput:
        return await _get_reservation_query_input_api(self._http_client, token, reservation_url)

    async def reserve(self, token: str, reservation_input: ReservationQueryInput) -> None:
        return await _reserve_api(self._http_client, token, reservation_input)

    async def get_user_account_info(self, token: str) -> UserAccountInfo:
        return await _get_account_info_api(self._http_client, token)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._http_client.aclose()
