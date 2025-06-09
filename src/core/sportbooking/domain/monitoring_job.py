from dataclasses import dataclass
from enum import Enum

from dataclasses_json import dataclass_json


class MonitoringAction(Enum):
    NOTIFY = "NOTIFY"
    RESERVE = "RESERVE"


@dataclass_json
@dataclass(frozen=True)
class MonitoringJob():
    action: MonitoringAction


@dataclass_json
@dataclass(frozen=True)
class MonitoringJobCreate():
    action: MonitoringAction
