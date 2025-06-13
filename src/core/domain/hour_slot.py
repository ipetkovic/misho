
from dataclasses import dataclass

from dataclasses_json import dataclass_json
import pydantic

type HourSlotId = int


class HourSlot(pydantic.BaseModel):
    from_hour: int
    to_hour: int

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
