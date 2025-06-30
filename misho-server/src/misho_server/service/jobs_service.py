from misho_server.domain.job import Job, JobCreate, Status
from misho_server.domain.user import UserId
from misho_server.repository.court import CourtRepository
from misho_server.repository.hour_slot import HourSlotRepository
from misho_server.repository.jobs import JobsRepository


class JobsServiceError(Exception):
    pass


class InvalidHourSlot(JobsServiceError):
    def __init__(self, message: str):
        super().__init__(message)


class InvalidCourts(JobsServiceError):
    def __init__(self, message: str):
        super().__init__(message)


class JobAlreadyExists(JobsServiceError):
    def __init__(self, message: str):
        super().__init__(message)


class JobsService:
    def __init__(
        self,
        jobs_repository: JobsRepository,
        hour_slots_repository: HourSlotRepository,
        court_repository: CourtRepository
    ):
        self._jobs_repository = jobs_repository
        self._hour_slots_repository = hour_slots_repository
        self._court_repository = court_repository

    async def create_job(self, job_create: JobCreate) -> Job:
        await self._validate_job_create(job_create)
        return await self._jobs_repository.insert(job_create)

    async def list_jobs(self, statuses: list[Status] | None = None, user_id: UserId = None) -> list[Job]:
        self._jobs_repository.list_all(statuses=statuses, user_id=user_id)

    async def get_job(self, job_id: int) -> Job | None:
        self._jobs_repository.find_by_id(job_id)

    async def delete_job(self, job_id: int) -> bool:
        job = await self.get_job(job_id)

        if not job:
            return False

        await self._jobs_repository.delete(job_id)
        return True

    async def _validate_job_create(self, job_create: JobCreate) -> bool:
        hour_slots = await self._hour_slots_repository.list_hour_slots()

        if job_create.time_slot.hour_slot not in hour_slots:
            hour_slots_pretty = ', '.join(str(slot) for slot in hour_slots)
            error = f"Invalid hour slot: {job_create.time_slot.hour_slot}. Available hour slots: {hour_slots_pretty}"
            raise InvalidHourSlot(error)

        courts = await self._court_repository.list_courts()
        diff = set(job_create.courts_by_priority) - \
            set(court.id for court in courts)

        if diff:
            error = f"Invalid courts: {diff}. Available courts: {[court.id for court in courts]}"
            raise InvalidCourts(error)

        job_for_time_slot = await self._jobs_repository.find_by_time_slot(job_create.time_slot)
        if job_for_time_slot:
            return JobAlreadyExists(
                f"Job for time slot {job_create.time_slot} already exists (id: {job_for_time_slot.id}). Either delete previous job or change time slot."
            )
