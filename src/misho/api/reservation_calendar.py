

import datetime
import pydantic

from misho.domain.hour_slot import HourSlot
from misho.domain.reservation_calendar import CourtId


class CourtInfo(pydantic.BaseModel):
    court_id: CourtId
    reserved_by: str | None = None
    reserved_by_user: bool = False

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class HourSlotReservation(pydantic.BaseModel):
    hour_slot: HourSlot
    courts: list[CourtInfo]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class DayReservation(pydantic.BaseModel):
    slots: list[HourSlotReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class UserReservationCalendar(pydantic.BaseModel):
    calendar: dict[datetime.date, DayReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
