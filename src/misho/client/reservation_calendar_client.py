

import httpx

from misho.api import Error
from misho.api.reservation_calendar import UserReservationCalendar
from misho.client import Authorization
from misho.domain.job import Status


class ReservationCalendarClient:
    def __init__(self, http_client: httpx.AsyncClient, base_url: str):
        self._http_client = http_client
        self._base_url = base_url

    async def get_calendar(self, authorization: Authorization, status: Status = None) -> UserReservationCalendar | Error:
        request = httpx.Request(
            method="GET",
            url=self._base_url + "/calendar",
            headers={"Authorization": authorization.to_header()},
        )
        response = await self._http_client.send(request)

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return UserReservationCalendar(**response.json())
