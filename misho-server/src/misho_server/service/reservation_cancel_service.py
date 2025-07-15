import logging
from misho_server.core.reservation_slot import ReservationSlot
from misho_server.core.reservation_update_bus import ReservationUpdateBus
from misho_server.core.reservation_update_event import ReservationUpdateEvent, ReservationUpdateEventType
from misho_server.service.sportbooking_service import SportbookingService
from misho_server.core.reservation_calendar import UserReservationCalendar
from misho_server.core.session_token import SessionToken
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from misho_server.config import CONFIG


class InvalidReservationSlot(Exception):
    def __init__(self, reservation_slot: ReservationSlot):
        super().__init__(f"Cannot cancel reservation slot: {reservation_slot}")


class ReservationCancelRequestFailed(Exception):
    def __init__(self, reservation_slot: ReservationSlot):
        super().__init__(
            f"Reservation cancel request failed for {reservation_slot}")


class ReservationCancelService:
    def __init__(
        self,
        sportbooking: SportbookingService,
        session_token_fetch_service: SessionTokenFetchService,
        reservation_update_bus: ReservationUpdateBus
    ):
        self._session_token_fetch_service = session_token_fetch_service
        self._sportbooking = sportbooking
        self._reservation_update_bus = reservation_update_bus

    async def cancel_reservation(self, user_id: int, reservation_slot: ReservationSlot) -> None:
        logging.info(
            f"Canceling reservation for user {user_id} on {reservation_slot.time_slot} for court {reservation_slot.court}")
        token = await self._session_token_fetch_service.get_token(user_id)
        calendar = await self.refresh_reservation_calendar(token)

        user_court_reservation = calendar.user_calendar.get(
            reservation_slot, None)

        if user_court_reservation is None:
            raise InvalidReservationSlot(reservation_slot)

        link_for_cancellation = user_court_reservation.link_for_cancellation
        if link_for_cancellation is None:
            raise InvalidReservationSlot(reservation_slot)

        logging.debug(
            f"Trying to cancel reservation for court {reservation_slot.court}")
        await self._cancel_reservation(
            user_token=token,
            reservation_slot=reservation_slot,
            link=link_for_cancellation
        )
        await self._reservation_update_bus.publish(ReservationUpdateEvent(
            user_id=user_id,
            event_type=ReservationUpdateEventType.CANCELLED,
        ))

    async def _cancel_reservation(
            self,
            user_token: SessionToken,
            reservation_slot: ReservationSlot,
            link: str
    ) -> None:
        logging.debug(
            f"Cancelling reservation for court {reservation_slot.court} for {reservation_slot.time_slot} at {link}")
        if CONFIG.dummy_reservation:
            logging.info(
                f"Dummy reservation cancellation for court {reservation_slot.court} on {reservation_slot.time_slot}")
        else:
            await self._sportbooking.cancel_reservation(user_token, link)
        await self._verify_cancellation(user_token, reservation_slot)

    async def _verify_cancellation(self, user_token: SessionToken, reservation_slot: ReservationSlot) -> None:
        if not CONFIG.dummy_reservation:
            logging.debug(
                f"Verifying reservation cancellation for court {reservation_slot.court} on {reservation_slot.time_slot}"
            )
            calendar = await self.refresh_reservation_calendar(user_token)
            if calendar.user_calendar[reservation_slot].reserved_by_user:
                raise ReservationCancelRequestFailed(reservation_slot)

    async def refresh_reservation_calendar(self, token: SessionToken) -> UserReservationCalendar:
        return await self._sportbooking.get_reservation_calendar(token)
