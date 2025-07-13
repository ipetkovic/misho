import datetime
import pydantic
from misho_server.domain.hour_slot import HourSlot

type TimeSlotId = int


class TimeSlot(pydantic.BaseModel):
    date: datetime.date
    hour_slot: HourSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)

    def start_time(self) -> datetime.datetime:
        return datetime.datetime.combine(self.date, datetime.time(self.hour_slot.from_hour))

    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')} {self.hour_slot.from_hour:02d}:00 - {self.hour_slot.to_hour:02d}:00"
