
import pydantic

type HourSlotId = int


class HourSlot(pydantic.BaseModel):
    from_hour: int
    to_hour: int

    def __str__(self):
        return f"{self.from_hour:02d}:00 - {self.to_hour:02d}:00"

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
