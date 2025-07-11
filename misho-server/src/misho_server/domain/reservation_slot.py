import pydantic

from misho_server.domain.court import CourtId
from misho_server.domain.time_slot import TimeSlot


class ReservationSlot(pydantic.BaseModel):
    time_slot: TimeSlot
    court: CourtId

    def __str__(self):
        return f"{self.time_slot} - Court {self.court}"

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
