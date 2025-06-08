
from dataclasses import dataclass

from dataclasses_json import dataclass_json

type HourSlotId = int


@dataclass_json
@dataclass(frozen=True)
class HourSlot:
    from_hour: int
    to_hour: int
