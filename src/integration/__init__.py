import httpx
from misho.sportbooking.integration import reservation_input
from misho.sportbooking.integration.login import LoginResponse
from misho.sportbooking.integration.reservation_calendar import get_reservation_calendar
from misho.sportbooking.domain.session_token import SessionToken
from misho.sportbooking.domain.reservation_calendar import UserReservationCalendar
from misho.sportbooking.integration.login import login as login_api
from misho.sportbooking.integration.reserve import reserve as reserve_api
from misho.sportbooking.integration.user_account import UserAccountInfo, get_account_info


class SportbookingApi:
    async def login(self, username: str, password: str) -> LoginResponse:
        raise NotImplementedError()

    async def get_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        raise NotImplementedError()

    async def get_reservation_query_input(self, token: SessionToken, reservation_url: str) -> reservation_input.ReservationQueryInput:
        raise NotImplementedError()

    async def reserve(self, token: SessionToken, reservation_input: reservation_input.ReservationQueryInput) -> None:
        raise NotImplementedError()

    async def get_user_account_info(self, token: SessionToken) -> UserAccountInfo:
        raise NotImplementedError()


class SportBookingApiImpl(SportbookingApi):
    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client

    async def login(self, username: str, password: str) -> LoginResponse:
        return await login_api(self._http_client, username, password)

    async def get_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        return await get_reservation_calendar(self._http_client, token)

    async def get_reservation_query_input(self, token: SessionToken, reservation_url: str) -> reservation_input.ReservationQueryInput:
        return await reservation_input.get_reservation_query_input(self._http_client, token, reservation_url)

    async def reserve(self, token: SessionToken, reservation_input: reservation_input.ReservationQueryInput) -> None:
        return await reserve_api(self._http_client, token, reservation_input)

    async def get_user_account_info(self, token: SessionToken) -> UserAccountInfo:
        return await get_account_info(self._http_client, token)
