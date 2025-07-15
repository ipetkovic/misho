from datetime import date
from misho_server.core.reservation_calendar import ReservationCalendar


class ReservationCalendarRepository:
    async def get_calendar(self, filter_by_name: str | None = None, filter_by_days: list[date] | None = None) -> ReservationCalendar | None:
        raise NotImplementedError()

    async def set_calendar(self, calendar: ReservationCalendar) -> None:
        raise NotImplementedError()
