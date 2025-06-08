from dataclasses import dataclass

type CourtId = int


@dataclass
class Court:
    id: CourtId
    name: str
