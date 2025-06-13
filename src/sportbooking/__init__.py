import httpx
from sportbooking import reservation_input
from sportbooking._internal.sportbooking_api import SportBookingApiImpl as _SportbookingApiImpl
from sportbooking.login import LoginResponse
from sportbooking.reservation_calendar import UserReservationCalendar
from sportbooking.user_account_info import UserAccountInfo


class SportbookingApi:
    async def login(self, username: str, password: str) -> LoginResponse:
        raise NotImplementedError()

    async def get_reservation_calendar(self, token: str) -> UserReservationCalendar:
        raise NotImplementedError()

    async def get_reservation_query_input(self, token: str, reservation_url: str) -> reservation_input.ReservationQueryInput:
        raise NotImplementedError()

    async def reserve(self, token: str, reservation_input: reservation_input.ReservationQueryInput) -> None:
        raise NotImplementedError()

    async def get_user_account_info(self, token: str) -> UserAccountInfo:
        raise NotImplementedError()


def create_sportbooking_api(http_client: httpx.AsyncClient) -> SportbookingApi:
    return _SportbookingApiImpl(http_client)
