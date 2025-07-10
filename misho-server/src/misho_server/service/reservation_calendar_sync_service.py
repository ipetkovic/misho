import logging
from misho_server.domain.reservation_calendar import ReservationCalendar
from misho_server.domain.user import UserId
from misho_server.repository.reservation_calendar import ReservationCalendarRepository
from misho_server.repository.user import UserRepository
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from misho_server.service.sportbooking_service import SportbookingService


type CalendarUpdated = bool


class ReservationCalendarSyncService:
    def __init__(
        self,
        reservation_calendar_repository: ReservationCalendarRepository,
        user_repository: UserRepository,
        token_fetch_service: SessionTokenFetchService,
        sporbooking_service: SportbookingService
    ):
        self._reservation_calendar_repository = reservation_calendar_repository
        self._user_repository = user_repository
        self._sportbooking_service = sporbooking_service
        self._token_fetch_service = token_fetch_service
        self._user_id: UserId | None = None

    async def sync_calendar(self) -> CalendarUpdated:
        logging.debug("Fetching reservation calendar")
        old_calendar = await self._reservation_calendar_repository.get_calendar()
        new_calendar = await self._fetch_calendar()

        diff = {}
        if old_calendar is not None:
            diff = new_calendar.diff(old_calendar)

        if old_calendar is not None and len(diff) == 0:
            logging.debug("Calendar has not changed")
            return False
        else:
            logging.debug("Calendar has changed")
            await self._reservation_calendar_repository.set_calendar(new_calendar)
            return True

    async def _fetch_calendar(self):
        user_id = await self._get_user_id()
        token = await self._token_fetch_service.get_token(user_id)
        calendar = await self._sportbooking_service.get_reservation_calendar(token)
        return ReservationCalendar.from_user_reservation_calendar(calendar)

    async def _get_user_id(self):
        if self._user_id is None:
            users = await self._user_repository.list_users()
            if not users:
                raise ValueError("No users found")
            logging.info(f'Using user {users[0].username} for calendar sync')
            self._user_id = users[0].id

        return self._user_id
