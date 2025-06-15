from misho_server.controller.transformers import time_slot_from_api, time_slot_to_api
from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.monitoring_job import MonitoringJob, MonitoringJobCreate
from misho_server.domain.time_slot import TimeSlot
from misho_api.hour_slot import HourSlotApi
from misho_api.job import JobApi, JobCreateApi, JobListApi
from misho_server.controller.common import bad_request, from_json, not_found, success_response
from misho_server.domain.job import Job as JobDomain, JobCreate as JobCreateDomain, JobId, Status
from misho_server.domain.user import User
from misho_server.repository.court import CourtRepository
from misho_server.repository.hour_slot import HourSlotRepository
from misho_server.repository.jobs import JobsRepository

from aiohttp import web

from misho_api.time_slot import TimeSlotApi


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
        return success_response(JobListApi(jobs=jobs_domain))

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
        print(f"Job create request: {body}")
        job_create = from_json(body, JobCreateApi)
        print(f"Job create request: {job_create}")
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

    async def _validate_job_create(self, job_create: JobCreateApi) -> bool:
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


def to_api_job(job: JobDomain) -> JobApi:
    job_api = JobApi(
        id=job.id,
        time_slot=time_slot_to_api(job.time_slot),
        courts_by_priority=job.courts_by_priority,
        action=job.job_type.action.value,
        created_at=job.created_at,
        status=job.status.value
    )
    return job_api


def to_api_job_create(job_create: JobCreateDomain) -> JobCreateApi:
    job_create_api = JobCreateApi(
        time_slot=time_slot_to_api(job_create.time_slot),
        action=job_create.job_type.action.value,
        courts_by_priority=list(job_create.courts_by_priority)
    )
    return job_create_api


def from_api_job(job: JobApi, user: User) -> JobDomain:
    job_domain = JobDomain(
        id=job.id,
        user=user,
        time_slot=time_slot_from_api(job.time_slot),
        courts_by_priority=job.courts_by_priority,
        job_type=MonitoringJob(action=job.action.value),
        created_at=job.created_at,
        status=Status(job.status.value),
    )
    return job_domain


def from_api_job_create(job_create: JobCreateApi, user: User) -> JobCreateDomain:
    job_create_domain = JobCreateDomain(
        user_id=user.id,
        time_slot=time_slot_from_api(job_create.time_slot),
        job_type=MonitoringJobCreate(action=job_create.action.value),
        courts_by_priority=tuple(job_create.courts_by_priority)
    )
    return job_create_domain
