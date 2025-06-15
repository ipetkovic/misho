import requests
from misho_api import Error
from misho_api.reservation_calendar import UserReservationCalendarApi
from misho_client import Authorization


class ReservationCalendarClient:
    def __init__(self, base_url: str):
        self._base_url = base_url

    def get_calendar(self, authorization: Authorization) -> UserReservationCalendarApi | Error:
        request = requests.Request(
            method="GET",
            url=self._base_url + "/calendar",
            headers={"Authorization": authorization.to_header()},
        )

        with requests.Session() as session:
            response = session.send(request.prepare())

        if response.status_code != 200:
            error = Error.from_json(response.text)
            return error

        return UserReservationCalendarApi(**response.json())
