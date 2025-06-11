from dataclasses import dataclass
import datetime
from enum import Enum

from dataclasses_json import dataclass_json
import pydantic

from core.sportbooking.domain.monitoring_job import MonitoringJob, MonitoringJobCreate
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.reserve_job import ReserveJob, ReserveJobCreate
from core.sportbooking.domain.time_slot import TimeSlot, TimeSlotId
from core.sportbooking.domain.user import User, UserId
from typing import TypeVar, Generic

type JobId = int


class Status(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


JobType = TypeVar('JobType', ReserveJob, MonitoringJob)


class Job(pydantic.BaseModel):
    id: JobId
    user: User
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    job_type: JobType
    created_at: datetime.datetime
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


# JobTypeCreate = TypeVar('JobTypeCreate', ReserveJobCreate, MonitoringJobCreate)


# @dataclass
class JobCreate(pydantic.BaseModel):
    user_id: UserId
    time_slot: TimeSlot
    job_type: MonitoringJobCreate
    courts_by_priority: list[CourtId]

    # extra = 'forbid'

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
