from dataclasses import dataclass
import datetime
import json

from dataclasses_json import dataclass_json
from pydantic_core import ErrorDetails
from core.sportbooking.api.common import SuccessResult
from core.sportbooking.domain.job import Job as JobDomain, JobCreate as JobCreateDomain, JobId, JobType, Status
from core.sportbooking.domain.monitoring_job import MonitoringAction, MonitoringJobCreate
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.time_slot import TimeSlot
from core.sportbooking.domain.user import User
from core.sportbooking.repository.jobs import JobsRepository

from aiohttp import request, web

import pydantic


class Job(pydantic.BaseModel):
    id: JobId
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId, ...]
    job_type: JobType
    created_at: datetime.datetime
    status: Status

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobCreate(pydantic.BaseModel):
    time_slot: TimeSlot
    job_type: MonitoringJobCreate
    courts_by_priority: list[CourtId]

    # extra = 'forbid'

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class JobsResult(SuccessResult):
    jobs: list[Job]


def to_api_job(job: JobDomain) -> Job:
    return Job(**job.model_dump(exclude={'user_id'}))


def to_api_job_create(job_create: JobCreateDomain) -> JobCreate:
    return JobCreate(**job_create.model_dump(exclude={'user_id'}))


def from_api_job(job: Job, user: User) -> JobDomain:
    return JobDomain(user=user, **job.model_dump())


def from_api_job_create(job_create: JobCreate, user: User) -> JobCreateDomain:
    return JobCreateDomain(user_id=user.id, **job_create.model_dump())


class JobsController:
    def __init__(self, jobs_repository: JobsRepository):
        self.jobs_repository = jobs_repository

    def get_routes(self):
        return [
            web.get('/jobs', self.list_jobs),
            web.get('/jobs/{job_id:\d+}', self.get_job),
            web.post('/jobs', self.create_job),
            web.delete('/jobs/{job_id:\d+}', self.delete_job),
        ]

    async def list_jobs(self, request: web.Request):
        status = request.query.get('status', None)
        if status is not None:
            status = self._convert_status(status)
            if status is None:
                error = FailureResult(
                    error=f"Invalid status: {status}. Supported values: PENDING, FAILED, SUCCESS")
                return web.json_response(status=400, body=to_json(error))

        jobs = await self.jobs_repository.list_all(status=status)
        jobs_domain = [to_api_job(job) for job in jobs]
        jobs_json = to_json(JobsResult(jobs=jobs_domain))
        return web.json_response(body=jobs_json)

    async def get_job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        job = await self.jobs_repository.find_by_id(job_id)
        if not job:
            error = FailureResult(error=f"Job with id {job_id} not found")
            return web.json_response(status=404, body=to_json(error))

        job_json = to_json(to_api_job(job))
        return web.json_response(body=job_json)

    async def create_job(self, request: web.Request):
        user = request['user']
        body = await request.json()
        job_create = from_json(body, JobCreate)
        job_create_domain = from_api_job_create(job_create, user)

        job_for_time_slot = await self.jobs_repository.find_by_time_slot(job_create_domain.time_slot)
        if job_for_time_slot:
            error = FailureResult(
                error=f"Job for time slot {job_create_domain.time_slot} already exists (id: {job_for_time_slot.id}). Either delete previous job or change time slot.")
            return web.json_response(status=400, body=to_json(error))

        job_domain = await self.jobs_repository.insert(job_create_domain)
        job_api = to_api_job(job_domain)
        return web.json_response(body=to_json(job_api))

    async def delete_job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        await self.jobs_repository.delete(job_id)
        return web.json_response()

    def _convert_status(self, status: str) -> Status:
        try:
            return Status(status)
        except ValueError:
            return None
