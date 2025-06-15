import datetime
import pydantic
from misho_server.domain.hour_slot import HourSlot

type TimeSlotId = int


class TimeSlot(pydantic.BaseModel):
    date: datetime.date
    hour_slot: HourSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} {self.hour_slot.from_hour:02d}:00 - {self.hour_slot.to_hour:02d}:00"
