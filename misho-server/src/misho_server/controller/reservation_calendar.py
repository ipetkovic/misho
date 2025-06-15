import datetime
from misho_server.controller.transformers import hour_slot_to_api
from misho_api.reservation_calendar import CourtInfo, DayReservation, HourSlotReservation, UserReservationCalendarApi
from misho_server.controller.common import bad_request, from_json, success_response
from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.reservation_calendar import UserReservationCalendar as UserReservationCalendarDomain
from misho_server.domain.user import UserCreate
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from misho_server.service.sportbooking_service import SportbookingService
from misho_server.repository.user import UserRepository
from aiohttp import web


class ReservationCalendarController:
    def __init__(self, sportbooking: SportbookingService, session_token_fetch_service: SessionTokenFetchService):
        self._sportbooking = sportbooking
        self._session_token_fetch_service = session_token_fetch_service

    def get_routes(self):
        return [
            web.get('/calendar', self.get_calendar),
        ]

    async def get_calendar(self, request: web.Request) -> UserReservationCalendarApi:
        user = request['user']
        token = await self._session_token_fetch_service.get_token(user.id)
        calendar = await self._sportbooking.get_reservation_calendar(token)
        calendar_api = from_domain(calendar)
        return success_response(calendar_api)


def from_domain(calendar: UserReservationCalendarDomain) -> UserReservationCalendarApi:
    transformed: dict[datetime.date, dict[HourSlot, list[CourtInfo]]] = {}
    for reservation_slot, reservation in calendar.user_calendar.items():
        date = reservation_slot.time_slot.date
        hour_slot = reservation_slot.time_slot.hour_slot
        court_id = reservation_slot.court

        reserved_by = reservation.reserved_by
        reserved_by_user = reservation.reserved_by_user

        if date not in transformed:
            transformed[date] = {}

        calendar_day = transformed[date]

        if hour_slot not in calendar_day:
            calendar_day[hour_slot] = []

        transformed[date][hour_slot].append(
            CourtInfo(
                court_id=court_id,
                reserved_by=reserved_by,
                reserved_by_user=reserved_by_user,
            )
        )

    calendar_api: dict[datetime.date, DayReservation] = {}
    for date, slots in transformed.items():
        hour_slot_reservation = [HourSlotReservation(hour_slot=hour_slot_to_api(hour_slot), courts=courts)
                                 for hour_slot, courts in slots.items()]
        calendar_api[date] = DayReservation(slots=hour_slot_reservation)

    return UserReservationCalendarApi(calendar=calendar_api)
