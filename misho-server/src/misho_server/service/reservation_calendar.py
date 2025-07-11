

from datetime import date
from misho_server.domain.reservation_calendar import ReservationCalendar
from misho_server.domain.user import UserId
from misho_server.repository.reservation_calendar import ReservationCalendarRepository
from misho_server.repository.user import UserRepository


class ReservationCalendarService:
    def __init__(
        self,
        reservation_calendar_repository: ReservationCalendarRepository,
        user_repository: UserRepository
    ):
        self._reservation_calendar_repository = reservation_calendar_repository
        self._user_repository = user_repository

    async def get_calendar(self, user_id: UserId | None = None, filter_by_days: list[date] | None = None) -> ReservationCalendar | None:
        name = None
        if user_id is not None:
            user = await self._user_repository.get_user_by_id(user_id)
            name = user.name if user else None
        result = await self._reservation_calendar_repository.get_calendar(name, filter_by_days)
        return result
