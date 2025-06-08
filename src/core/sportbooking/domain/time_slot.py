from dataclasses import dataclass
import datetime

from core.sportbooking.domain.hour_slot import HourSlot

type TimeSlotId = int


@dataclass(frozen=True)
class TimeSlot:
    date: datetime.datetime
    hour_slot: HourSlot

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} {self.hour_slot.from_hour:02d}:00 - {self.hour_slot.to_hour:02d}:00"
