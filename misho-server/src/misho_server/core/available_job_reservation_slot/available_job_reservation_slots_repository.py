from dataclasses import dataclass
from misho_server.core.court import CourtId
from misho_server.core.job import Job


@dataclass(frozen=True)
class AvailableJobReservationSlot:
    job: Job
    court_id: CourtId


class AvailableJobReservationSlotRepository:
    async def get_available_job_reservation_slots(self) -> list[AvailableJobReservationSlot]:
        raise NotImplementedError()
