

import datetime
import pydantic

from misho.domain.hour_slot import HourSlot
from misho.domain.reservation_calendar import CourtId


class Slot(pydantic.BaseModel):
    hour_slot: HourSlot
    court_id: CourtId
    reserved_by: str | None = None
    reserved_by_user: bool = False

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class UserReservationCalendar(pydantic.BaseModel):
    calendar: dict[datetime.date, list[Slot]]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
