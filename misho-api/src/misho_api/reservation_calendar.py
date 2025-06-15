import datetime
import pydantic
from misho_api.hour_slot import HourSlotApi


class CourtInfo(pydantic.BaseModel):
    court_id: int
    reserved_by: str | None = None
    reserved_by_user: bool = False

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class HourSlotReservation(pydantic.BaseModel):
    hour_slot: HourSlotApi
    courts: list[CourtInfo]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class DayReservation(pydantic.BaseModel):
    slots: list[HourSlotReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class UserReservationCalendarApi(pydantic.BaseModel):
    calendar: dict[datetime.date, DayReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
