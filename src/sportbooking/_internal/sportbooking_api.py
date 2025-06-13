import httpx
from sportbooking import SportbookingApi, reservation_input
from sportbooking.login import LoginResponse
from sportbooking.reservation_calendar import UserReservationCalendar, get_reservation_calendar
from sportbooking._internal.login import login as login_api
from sportbooking._internal.reserve import reserve as reserve_api
from sportbooking._internal.user_account import get_account_info
from sportbooking.user_account_info import UserAccountInfo


class SportBookingApiImpl(SportbookingApi):
    def __init__(self, http_client: httpx.AsyncClient):
        self._http_client = http_client

    async def login(self, username: str, password: str) -> LoginResponse:
        return await login_api(self._http_client, username, password)

    async def get_reservation_calendar(self, token: str) -> UserReservationCalendar:
        return await get_reservation_calendar(self._http_client, token)

    async def get_reservation_query_input(self, token: str, reservation_url: str) -> reservation_input.ReservationQueryInput:
        return await reservation_input.get_reservation_query_input(self._http_client, token, reservation_url)

    async def reserve(self, token: str, reservation_input: reservation_input.ReservationQueryInput) -> None:
        return await reserve_api(self._http_client, token, reservation_input)

    async def get_user_account_info(self, token: str) -> UserAccountInfo:
        return await get_account_info(self._http_client, token)
