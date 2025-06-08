from dataclasses import dataclass

from core.sportbooking.domain.job import JobId
from core.sportbooking.domain.reservation_slot import ReservationSlot

type JobNotificationId = int


@dataclass(frozen=True)
class JobNotification:
    job_notification_id: JobNotificationId
    job_id: JobId
    reservation_slot: ReservationSlot
    reserved_by: str | None

    def is_available(self) -> bool:
        return self.reserved_by is None
