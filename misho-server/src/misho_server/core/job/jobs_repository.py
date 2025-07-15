import datetime

from misho_server.core.job import Job, JobCreate, JobId, Status
from misho_server.core.user import UserId
from misho_server.core.time_slot import TimeSlot


class JobsRepository:
    async def insert(self, job: JobCreate) -> Job:
        raise NotImplementedError()

    async def find_by_id(self, job_id: JobId) -> Job | None:
        raise NotImplementedError()

    async def find_by_time_slot(
        self, time_slot: TimeSlot, user_id: UserId | None = None
    ) -> Job | None:
        raise NotImplementedError()

    async def list_all(self, statuses: list[Status] | None = None, user_id: UserId | None = None) -> list[Job]:
        raise NotImplementedError()

    async def get_reservation_jobs_for_date(self, date: datetime.date) -> list[Job]:
        raise NotImplementedError()

    async def update_job_status(self, job_id: JobId, status: Status) -> None:
        raise NotImplementedError()

    async def delete(self, job_id: JobId) -> None:
        raise NotImplementedError()
