import datetime
from enum import Enum

import pydantic

from misho_server.domain.reservation_calendar import CourtId
from misho_server.domain.time_slot import TimeSlot
from misho_server.domain.user import User, UserId

type JobId = int


class Status(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobAction(Enum):
    RESERVE = "RESERVE"
    NOTIFY = "NOTIFY"


class Job(pydantic.BaseModel):
    id: JobId
    user: User
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    action: JobAction
    created_at: datetime.datetime
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreate(pydantic.BaseModel):
    user_id: UserId
    time_slot: TimeSlot
    action: JobAction
    courts_by_priority: list[CourtId]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
