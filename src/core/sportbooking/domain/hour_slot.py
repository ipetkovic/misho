
from dataclasses import dataclass

type HourSlotId = int


@dataclass(frozen=True)
class HourSlot:
    from_hour: int
    to_hour: int
