import datetime
import pydantic
from misho_server.core.hour_slot import HourSlot

type TimeSlotId = int


class TimeSlot(pydantic.BaseModel):
    date: datetime.date
    hour_slot: HourSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)

    def start_time(self) -> datetime.datetime:
        return datetime.datetime.combine(self.date, datetime.time(self.hour_slot.from_hour))

    def __str__(self):
        return f"{self._day_name}, {self.date.strftime('%d.%m.%Y')} {self.hour_slot.from_hour:02d}:00 - {self.hour_slot.to_hour:02d}:00"

    def _day_name(self) -> str:
        day_names = {
            0: "Ponedjeljak",
            1: "Utorok",
            2: "Srijeda",
            3: "Četvrtak",
            4: "Petak",
            5: "Subota",
            6: "Nedjelja"
        }
        return day_names[self.date.weekday()]
