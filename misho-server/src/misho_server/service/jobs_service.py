from datetime import timedelta
import datetime
from misho_server.config.model import JobCreateConfig
from misho_server.core.job import Job, JobAction, JobCreate, Status
from misho_server.core.user import UserId
from misho_server.core.court.court_repository import CourtRepository
from misho_server.core.hour_slot.hour_slot_repository import HourSlotRepository
from misho_server.core.job.jobs_repository import JobsRepository


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
        job_create_config: JobCreateConfig,
        jobs_repository: JobsRepository,
        hour_slots_repository: HourSlotRepository,
        court_repository: CourtRepository
    ):
        self._job_create_config = job_create_config
        self._jobs_repository = jobs_repository
        self._hour_slots_repository = hour_slots_repository
        self._court_repository = court_repository

    async def create_job(self, job_create: JobCreate) -> Job:
        await self._validate_job_create(job_create)
        expires_at = self._get_job_expires_at(job_create)
        return await self._jobs_repository.insert(job_create.model_copy(
            update={"expires_at": expires_at, }
        ))

    async def list_jobs(self, statuses: list[Status] | None = None, user_id: UserId | None = None) -> list[Job]:
        result = await self._jobs_repository.list_all(statuses=statuses, user_id=user_id)
        return result

    async def get_job(self, job_id: int, user_id: UserId | None = None) -> Job | None:
        job = await self._jobs_repository.find_by_id(job_id)

        if not job or (user_id and job.user.id != user_id):
            return None
        return job

    async def delete_job(self, job_id: int, user_id: UserId | None) -> bool:
        job = await self.get_job(job_id, user_id)

        if not job or (user_id and job.user.id != user_id):
            return False

        await self._jobs_repository.delete(job_id)
        return True

    def _get_job_expires_at(self, job_create: JobCreate) -> datetime.datetime:
        job_expires_at = job_create.expires_at
        if job_expires_at is None:
            job_expires_at = job_create.time_slot.start_time()
            if job_create.action == JobAction.RESERVE:
                job_expires_at = job_create.time_slot.start_time() - \
                    timedelta(
                        hours=self._job_create_config.default_reserve_job_expire_before_hours)

        return job_expires_at

    async def _validate_job_create(self, job_create: JobCreate) -> None:
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

        job_for_time_slot = await self._jobs_repository.find_by_time_slot(job_create.time_slot, job_create.user_id)
        if job_for_time_slot:
            raise JobAlreadyExists(
                f"Job for time slot {job_create.time_slot} already exists (id: {job_for_time_slot.id}). Either delete previous job or change time slot."
            )

        if job_create.expires_at is not None and job_create.expires_at > job_create.time_slot.start_time():
            raise JobsServiceError(
                "Job expiration time must be before the start time of the time slot."
            )

        if job_create.on_expiry_action is not None and job_create.expires_at is None:
            raise JobsServiceError(
                "Job on expiry action is set, but expires_at is not set. Please set expires_at."
            )
