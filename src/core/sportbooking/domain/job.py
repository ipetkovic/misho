from dataclasses import dataclass
import datetime
from enum import Enum

from core.sportbooking.domain.monitoring_job import MonitoringJob, MonitoringJobCreate
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.reserve_job import ReserveJob, ReserveJobCreate
from core.sportbooking.domain.time_slot import TimeSlot, TimeSlotId
from core.sportbooking.domain.user import UserId
from typing import TypeVar, Generic

type JobId = int


class Status(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


JobType = TypeVar('JobType', ReserveJob, MonitoringJob)


@dataclass(frozen=True)
class Job(Generic[JobType]):
    id: JobId
    user_id: UserId
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId]
    job_type: JobType
    created_at: datetime.datetime
    status: Status


JobTypeCreate = TypeVar('JobTypeCreate', ReserveJobCreate, MonitoringJobCreate)


@dataclass
class JobCreate(Generic[JobTypeCreate]):
    user_id: UserId
    time_slot: TimeSlot
    job_type: JobTypeCreate
    courts_by_priority: list[CourtId]
