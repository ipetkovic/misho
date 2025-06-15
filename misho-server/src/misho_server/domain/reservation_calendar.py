from dataclasses import dataclass

import pydantic
from misho_server.domain.reservation_slot import ReservationSlot

type CourtId = int


class UserCourtReservation(pydantic.BaseModel):
    reserved_by: str | None
    reserved_by_user: bool
    link_for_reservation: str | None
    link_for_cancellation: str | None

    @property
    def is_available(self) -> bool:
        return self.reserved_by is None

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class CourtReservation(pydantic.BaseModel):
    reserved_by: str | None

    @property
    def is_available(self) -> bool:
        return self.reserved_by is None


class ReservationCalendar(pydantic.BaseModel):
    calendar: dict[ReservationSlot, CourtReservation]

    @staticmethod
    def from_user_reservation_calendar(
            user_calendar: 'UserReservationCalendar') -> 'ReservationCalendar':
        return ReservationCalendar(
            calendar={
                slot: CourtReservation(
                    reserved_by=user_court_reservation.reserved_by
                )
                for slot, user_court_reservation in user_calendar.user_calendar.items()
            }
        )

    def diff(self, other: 'ReservationCalendar') -> dict[ReservationSlot, CourtReservation]:
        diff = {}
        for slot, court_reservation in self.calendar.items():
            if slot not in other.calendar:
                diff[slot] = court_reservation
                continue
            other_court_reservation = other.calendar[slot]
            if court_reservation != other_court_reservation:
                diff[slot] = court_reservation
        return diff


class UserReservationCalendar(pydantic.BaseModel):
    user_calendar: dict[ReservationSlot, UserCourtReservation]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
