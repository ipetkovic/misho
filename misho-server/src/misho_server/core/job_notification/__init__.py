import pydantic

from misho_server.core.job import Job
from misho_server.core.reservation_slot import ReservationSlot

type JobNotificationId = int


class JobNotification(pydantic.BaseModel):
    job_notification_id: JobNotificationId
    job: Job
    reservation_slot: ReservationSlot
    reserved_by: str | None

    def is_available(self) -> bool:
        return self.reserved_by is None
