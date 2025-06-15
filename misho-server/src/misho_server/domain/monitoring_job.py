from enum import Enum
import pydantic


class MonitoringAction(Enum):
    NOTIFY = "NOTIFY"
    RESERVE = "RESERVE"


class MonitoringJob(pydantic.BaseModel):
    action: MonitoringAction

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class MonitoringJobCreate(pydantic.BaseModel):
    action: MonitoringAction

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
