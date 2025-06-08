from dataclasses import dataclass

from core.sportbooking.domain.court import CourtId
from core.sportbooking.domain.time_slot import TimeSlot


@dataclass(frozen=True)
class ReservationSlot:
    time_slot: TimeSlot
    court: CourtId
