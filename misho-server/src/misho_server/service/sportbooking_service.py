

from pydantic import TypeAdapter, parse_obj_as
import pydantic
from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.reservation_calendar import UserCourtReservation, UserReservationCalendar
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.domain.session_token import SessionToken
from misho_server.domain.time_slot import TimeSlot
from sportbooking import SportbookingApi
import sportbooking
import sportbooking.reservation_calendar


class SportbookingService:
    async def login(self, username: str, password: str) -> SessionToken:
        raise NotImplementedError()

    async def get_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        raise NotImplementedError()

    async def reserve(self, token: SessionToken, reservation_url: str) -> None:
        raise NotImplementedError()

    async def get_user_account_name(self, token: SessionToken) -> str:
        raise NotImplementedError()


class SportbookingServiceImpl(SportbookingService):
    def __init__(self, sportbooking_api: SportbookingApi):
        self._sportbooking_api = sportbooking_api

    async def login(self, username: str, password: str) -> SessionToken:
        result = await self._sportbooking_api.login(username, password)
        return SessionToken(value=result.token)

    async def get_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        result = await self._sportbooking_api.get_reservation_calendar(token.value)
        return _user_reservation_calendar_to_domain(result)

    async def reserve(self, token: SessionToken, reservation_url: str) -> None:
        reservation_input = await self._sportbooking_api.get_reservation_query_input(token.value, reservation_url)
        await self._sportbooking_api.reserve(token.value, reservation_input)

    async def get_user_account_name(self, token: SessionToken) -> str:
        return (await self._sportbooking_api.get_user_account_info(token.value)).name


def _user_reservation_calendar_to_domain(
        user_reservation_calendar: sportbooking.reservation_calendar.UserReservationCalendar) -> UserReservationCalendar:
    reservations = {
        _reservation_slot_to_domain(slot): _user_court_reservation_to_domain(reservation)
        for slot, reservation in user_reservation_calendar.user_calendar.items()
    }
    return UserReservationCalendar(user_calendar=reservations)


def _hour_slot_to_domain(hour_slot: sportbooking.reservation_calendar.HourSlot) -> HourSlot:
    return HourSlot(**hour_slot.model_dump())


def _time_slot_to_domain(time_slot: sportbooking.reservation_calendar.TimeSlot) -> TimeSlot:
    return TimeSlot(
        date=time_slot.date,
        hour_slot=_hour_slot_to_domain(time_slot.hour_slot)
    )


def _reservation_slot_to_domain(reservation_slot: sportbooking.reservation_calendar.ReservationSlot) -> ReservationSlot:
    return ReservationSlot(
        time_slot=_time_slot_to_domain(reservation_slot.time_slot),
        court=reservation_slot.court,
    )


def _user_court_reservation_to_domain(
        user_court_reservation: sportbooking.reservation_calendar.UserCourtReservation) -> UserCourtReservation:
    return UserCourtReservation(**user_court_reservation.model_dump())
