from dataclasses import dataclass
from enum import Enum


class MonitoringAction(Enum):
    NOTIFY = "NOTIFY"
    RESERVE = "RESERVE"


@dataclass(frozen=True)
class MonitoringJob():
    action: MonitoringAction


@dataclass(frozen=True)
class MonitoringJobCreate():
    action: MonitoringAction
