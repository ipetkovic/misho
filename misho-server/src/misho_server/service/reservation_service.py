from dataclasses import dataclass
import datetime
import logging
from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.service.sportbooking_service import SportbookingService
from misho_server.domain.reservation_calendar import CourtId, UserReservationCalendar
from misho_server.domain.session_token import SessionToken
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from misho_server.config import CONFIG


@dataclass
class CourtNotAvailable(Exception):
    def __init__(self, request: ReservationSlot):
        super().__init__(
            f"Court {request.court} is not available for {request.time_slot}")


class CourtNotAvailableForUser(Exception):
    def __init__(self, request: ReservationSlot):
        super().__init__(
            f"Court {request.court} is not available for user on {request.time_slot}")


class DateNotAvailable(Exception):
    def __init__(self, date: datetime.date):
        super().__init__(f"Date {date} is not available for reservation")


class ReservationRequestFailed(Exception):
    def __init__(self, reservation_slot: ReservationSlot):
        super().__init__(
            f"Reservation request failed for court {reservation_slot.court} on {reservation_slot.time_slot}")


class ReservationService:
    def __init__(self, sportbooking: SportbookingService, session_token_fetch_service: SessionTokenFetchService):
        self._session_token_fetch_service = session_token_fetch_service
        self._sportbooking = sportbooking

    async def reserve(self, user_id: int, reservation_slot: ReservationSlot) -> None:
        logging.debug(
            f"Reserving for user {user_id} on {reservation_slot.time_slot} for court {reservation_slot.court}")
        token = await self._session_token_fetch_service.get_token(user_id)
        calendar = await self.refresh_reservation_calendar(token)

        date_available = reservation_slot.time_slot.date in [
            reservation_slot.time_slot.date
            for reservation_slot in calendar.user_calendar
        ]

        if not date_available:
            raise DateNotAvailable(reservation_slot.time_slot.date)

        if reservation_slot not in calendar.user_calendar.keys():
            raise CourtNotAvailable(reservation_slot)

        if calendar.user_calendar[reservation_slot].link_for_reservation is None:
            raise CourtNotAvailableForUser(reservation_slot)

        reservation_link = calendar.user_calendar[reservation_slot].link_for_reservation
        logging.debug(f"Trying to reserve court {reservation_slot.court}")
        return await self._reserve(
            user_token=token,
            reservation_slot=reservation_slot,
            link=reservation_link
        )

    async def _reserve(
            self,
            user_token: SessionToken,
            reservation_slot: ReservationSlot,
            link: str
    ) -> None:
        logging.debug(
            f"Reserving court {reservation_slot.court} for {reservation_slot.time_slot} at {link}")
        if CONFIG.dummy_reservation:
            logging.info(
                f"Dummy reservation for court {reservation_slot.court} on {reservation_slot.time_slot}")
        else:
            print("jaje")
            await self._sportbooking.reserve(user_token, link)
            print("jaje2")
        await self._verify_reservation(user_token, reservation_slot)

    async def _verify_reservation(self, user_token: SessionToken, reservation_slot: ReservationSlot) -> None:
        if CONFIG.dummy_reservation:
            logging.debug(
                f"Verifying reservation for court {reservation_slot.court} on {reservation_slot.time_slot}"
            )
            calendar = await self.refresh_reservation_calendar(user_token)
            if not calendar.user_calendar[reservation_slot].reserved_by_user:
                raise ReservationRequestFailed(reservation_slot)

    async def refresh_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        return await self._sportbooking.get_reservation_calendar(token)
