from dataclasses import dataclass
from enum import Enum

from dataclasses_json import dataclass_json
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
