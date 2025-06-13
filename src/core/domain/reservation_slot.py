from dataclasses import dataclass

import pydantic

from core.domain.court import CourtId
from core.domain.time_slot import TimeSlot


class ReservationSlot(pydantic.BaseModel):
    time_slot: TimeSlot
    court: CourtId

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
