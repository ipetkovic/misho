from misho.api.job import Job, JobCreate, JobsResult
from misho.controller.common import bad_request, from_json, not_found, success_response
from misho.domain.job import Job as JobDomain, JobCreate as JobCreateDomain, JobId, Status
from misho.domain.user import User
from misho.repository.court import CourtRepository
from misho.repository.hour_slot import HourSlotRepository
from misho.repository.jobs import JobsRepository

from aiohttp import web


def to_api_job(job: JobDomain) -> Job:
    return Job(**job.model_dump(exclude={'user_id'}))


def to_api_job_create(job_create: JobCreateDomain) -> JobCreate:
    return JobCreate(**job_create.model_dump(exclude={'user_id'}))


def from_api_job(job: Job, user: User) -> JobDomain:
    return JobDomain(user=user, **job.model_dump())


def from_api_job_create(job_create: JobCreate, user: User) -> JobCreateDomain:
    return JobCreateDomain(user_id=user.id, **job_create.model_dump())


class JobsController:
    def __init__(
        self,
        jobs_repository: JobsRepository,
        hour_slots_repository: HourSlotRepository,
        court_repository: CourtRepository
    ):
        self.jobs_repository = jobs_repository
        self._hour_slots_repository = hour_slots_repository
        self._court_repository = court_repository

    def get_routes(self):
        return [
            web.get('/jobs', self.list_jobs),
            web.get('/jobs/{job_id:\d+}', self.get_job),
            web.post('/jobs', self.create_job),
            web.delete('/jobs/{job_id:\d+}', self.delete_job),
        ]

    async def list_jobs(self, request: web.Request):
        user = request['user']
        status = request.query.get('status', None)
        status_enum = None
        if status is not None:
            status_enum = self._convert_status(status)
            if status_enum is None:
                return bad_request(
                    f"Invalid status: {status}. Supported values: PENDING, FAILED, SUCCESS"
                )

        jobs = await self.jobs_repository.list_all(status=status_enum, user_id=user.id)
        jobs_domain = [to_api_job(job) for job in jobs]
        return success_response(JobsResult(jobs=jobs_domain))

    async def get_job(self, request: web.Request):
        user: User = request['user']
        job_id = int(request.match_info['job_id'])
        job = await self.jobs_repository.find_by_id(job_id)
        if not job or job.user.id != user.id:
            return not_found(f"Job with id {job_id} not found")

        return success_response(to_api_job(job))

    async def create_job(self, request: web.Request):
        user: User = request['user']
        body = await request.json()
        job_create = from_json(body, JobCreate)
        job_create_domain = from_api_job_create(job_create, user)

        await self._validate_job_create(job_create=job_create_domain)

        job_for_time_slot = await self.jobs_repository.find_by_time_slot(job_create_domain.time_slot)
        if job_for_time_slot:
            return bad_request(
                f"Job for time slot {job_create_domain.time_slot} already exists (id: {job_for_time_slot.id}). Either delete previous job or change time slot."
            )

        job_domain = await self.jobs_repository.insert(job_create_domain)
        job_api = to_api_job(job_domain)
        return success_response(job_api)

    async def delete_job(self, request: web.Request):
        user = request['user']
        job_id = int(request.match_info['job_id'])

        job = await self.jobs_repository.find_by_id(job_id)
        if not job or job.user.id != user.id:
            return not_found(f"Job with id {job_id} not found")

        await self.jobs_repository.delete(job_id)
        return web.json_response()

    def _convert_status(self, status: str) -> Status:
        try:
            return Status(status)
        except ValueError:
            return None

    async def _validate_job_create(self, job_create: JobCreate) -> bool:
        hour_slots = await self._hour_slots_repository.list_hour_slots()

        if job_create.time_slot.hour_slot not in hour_slots:
            hour_slots_pretty = ', '.join(str(slot) for slot in hour_slots)
            error = f"Invalid hour slot: {job_create.time_slot.hour_slot}. Available hour slots: {hour_slots_pretty}"
            raise bad_request(error)

        courts = await self._court_repository.list_courts()
        diff = set(job_create.courts_by_priority) - \
            set(court.id for court in courts)

        if diff:
            error = f"Invalid courts: {diff}. Available courts: {[court.id for court in courts]}"
            raise bad_request(error)
