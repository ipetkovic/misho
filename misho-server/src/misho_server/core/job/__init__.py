import datetime
from enum import Enum

import pydantic

from misho_server.core.reservation_calendar import CourtId
from misho_server.core.time_slot import TimeSlot
from misho_server.core.user import User, UserId

type JobId = int


class Status(Enum):
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobAction(Enum):
    RESERVE = "RESERVE"
    NOTIFY = "NOTIFY"


class OnExpiryAction(Enum):
    CREATE_NOTIFY_JOB = "CREATE_NOTIFY_JOB"


class Job(pydantic.BaseModel):
    id: JobId
    user: User
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    action: JobAction
    created_at: datetime.datetime
    expires_at: datetime.datetime
    on_expiry_action: OnExpiryAction | None
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreate(pydantic.BaseModel):
    user_id: UserId
    time_slot: TimeSlot
    action: JobAction
    courts_by_priority: list[CourtId]
    expires_at: datetime.datetime | None = None
    on_expiry_action: OnExpiryAction | None = None

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
