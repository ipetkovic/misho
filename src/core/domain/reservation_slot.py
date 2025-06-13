from dataclasses import dataclass

import pydantic

from core.sportbooking.domain.court import CourtId
from core.sportbooking.domain.time_slot import TimeSlot


class ReservationSlot(pydantic.BaseModel):
    time_slot: TimeSlot
    court: CourtId

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
