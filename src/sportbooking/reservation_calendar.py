import datetime
import pydantic


type CourtId = int


class HourSlot(pydantic.BaseModel):
    from_hour: int
    to_hour: int

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class TimeSlot(pydantic.BaseModel):
    date: datetime.date
    hour_slot: HourSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class ReservationSlot(pydantic.BaseModel):
    time_slot: TimeSlot
    court: CourtId

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class UserCourtReservation(pydantic.BaseModel):
    reserved_by: str | None
    reserved_by_user: bool
    link_for_reservation: str | None
    link_for_cancellation: str | None

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class UserReservationCalendar(pydantic.BaseModel):
    user_calendar: dict[ReservationSlot, UserCourtReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
