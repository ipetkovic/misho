import pydantic
from misho.api.reservation_calendar import Slot, UserReservationCalendar
from misho.controller.common import bad_request, from_json, success_response
from misho.api.user import User
from misho.domain.reservation_calendar import UserReservationCalendar as UserReservationCalendarDomain
from misho.domain.user import UserCreate
from misho.service.session_token_fetch_service import SessionTokenFetchService
from misho.service.sportbooking_service import SportbookingService
from misho.repository.user import UserRepository
from aiohttp import web


class ReservationCalendarController:
    def __init__(self, sportbooking: SportbookingService, session_token_fetch_service: SessionTokenFetchService):
        self._sportbooking = sportbooking
        self._session_token_fetch_service = session_token_fetch_service

    def get_routes(self):
        return [
            web.get('/calendar', self.get_calendar),
        ]

    async def get_calendar(self, request: web.Request) -> UserReservationCalendar:
        user = request['user']
        token = await self._session_token_fetch_service.get_token(user.id)
        calendar = await self._sportbooking.get_reservation_calendar(token)
        calendar_api = from_domain(calendar)
        return success_response(calendar_api)


def from_domain(calendar: UserReservationCalendarDomain) -> UserReservationCalendar:
    calendar_api = {}
    for reservation_slot, reservation in calendar.user_calendar.items():
        date = reservation_slot.time_slot.date
        hour_slot = reservation_slot.time_slot.hour_slot
        court_id = reservation_slot.court

        reserved_by = reservation.reserved_by
        reserved_by_user = reservation.reserved_by_user

        if date not in calendar_api:
            calendar_api[date] = []

        calendar_api[date].append(
            Slot(
                hour_slot=hour_slot,
                court_id=court_id,
                reserved_by=reserved_by,
                reserved_by_user=reserved_by_user,
            )
        )

    return UserReservationCalendar(calendar=calendar_api)
