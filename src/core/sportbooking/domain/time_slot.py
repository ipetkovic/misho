from dataclasses import dataclass, field
import datetime

from dataclasses_json import config, dataclass_json
from marshmallow import fields

from core.sportbooking.domain.hour_slot import HourSlot

type TimeSlotId = int


@dataclass_json
@dataclass(frozen=True)
class TimeSlot:
    date: datetime.date = field(
        metadata=config(
            encoder=datetime.date.isoformat,
            decoder=datetime.date.fromisoformat,
            mm_field=fields.Date(format='iso')
        )
    )
    hour_slot: HourSlot

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} {self.hour_slot.from_hour:02d}:00 - {self.hour_slot.to_hour:02d}:00"
