from dataclasses import dataclass

import pydantic

type CourtId = int


class Court(pydantic.BaseModel):
    id: CourtId
    name: str
