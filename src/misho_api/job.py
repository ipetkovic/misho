
import datetime
from enum import Enum
import pydantic

from misho_api.time_slot import TimeSlotApi


class ActionApi(Enum):
    RESERVE = "RESERVE"
    NOTIFY = "NOTIFY"


type JobIdApi = int
type CourtIdApi = int


class StatusApi(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobApi(pydantic.BaseModel):
    id: JobIdApi
    time_slot: TimeSlotApi
    courts_by_priority: tuple[CourtIdApi, ...]
    action: ActionApi
    created_at: datetime.datetime
    status: StatusApi

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreateApi(pydantic.BaseModel):
    time_slot: TimeSlotApi
    action: ActionApi
    courts_by_priority: list[CourtIdApi]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobListApi(pydantic.BaseModel):
    jobs: list[JobApi]

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
