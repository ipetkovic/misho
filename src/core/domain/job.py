import datetime
from enum import Enum

import pydantic

from core.domain.monitoring_job import MonitoringJob, MonitoringJobCreate
from core.domain.reservation_calendar import CourtId
from core.domain.time_slot import TimeSlot
from core.domain.user import User, UserId

type JobId = int


class Status(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Job(pydantic.BaseModel):
    id: JobId
    user: User
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    job_type: MonitoringJob
    created_at: datetime.datetime
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreate(pydantic.BaseModel):
    user_id: UserId
    time_slot: TimeSlot
    job_type: MonitoringJobCreate
    courts_by_priority: list[CourtId]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
