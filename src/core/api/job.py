
import datetime
import pydantic

from core.domain.job import JobId, Status
from core.domain.monitoring_job import MonitoringJob, MonitoringJobCreate
from core.domain.time_slot import TimeSlot
from sportbooking.reservation_calendar import CourtId


class Job(pydantic.BaseModel):
    id: JobId
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    job_type: MonitoringJob
    created_at: datetime.datetime
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreate(pydantic.BaseModel):
    time_slot: TimeSlot
    job_type: MonitoringJobCreate
    courts_by_priority: list[CourtId]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobsResult(pydantic.BaseModel):
    jobs: list[Job]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
