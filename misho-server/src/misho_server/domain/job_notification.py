from dataclasses import dataclass

import pydantic

from misho_server.domain.job import Job
from misho_server.domain.reservation_slot import ReservationSlot

type JobNotificationId = int


class JobNotification(pydantic.BaseModel):
    job_notification_id: JobNotificationId
    job: Job
    reservation_slot: ReservationSlot
    reserved_by: str | None

    def is_available(self) -> bool:
        return self.reserved_by is None
