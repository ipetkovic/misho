from dataclasses import dataclass
import datetime
import json

from dataclasses_json import dataclass_json
from pydantic_core import ErrorDetails
from core.sportbooking.domain.job import Job, JobCreate, JobId, Status
from core.sportbooking.domain.monitoring_job import MonitoringAction
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.time_slot import TimeSlot
from core.sportbooking.repository.jobs import JobsRepository

from aiohttp import web

import pydantic


class SuccessResult(pydantic.BaseModel):
    pass


class FailureResult(pydantic.BaseModel):
    error: str


class JobsResult(SuccessResult):
    jobs: list[Job]


class ValidationErrorResponse(pydantic.BaseModel):
    errors: list[ErrorDetails]


def to_json(obj: pydantic.BaseModel) -> str:
    return obj.model_dump_json(indent=2)


def from_json(body: any, cls: pydantic.BaseModel):
    try:
        return cls(**body)
    except pydantic.ValidationError as e:
        raise validation_error(e)


def validation_error(e: pydantic.ValidationError) -> web.HTTPBadRequest:
    json = to_json(ValidationErrorResponse(errors=e.errors()))
    return web.HTTPBadRequest(text=json)


class JobsController:
    def __init__(self, jobs_repository: JobsRepository):
        self.jobs_repository = jobs_repository

    def register_routes(self, app: web.Application):
        app.add_routes([
            web.get('/jobs', self.list_jobs),
            web.get('/jobs/{job_id:\d+}', self.get_job),
            web.post('/jobs', self.create_job),
            web.delete('/jobs/{job_id:\d+}', self.delete_job),
        ])

    async def list_jobs(self, _):
        jobs = await self.jobs_repository.list_all()
        print(jobs)
        jobs_json = to_json(JobsResult(jobs=jobs))
        print(jobs_json)
        return web.json_response(body=jobs_json)

    async def get_job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        job = await self.jobs_repository.find_by_id(job_id)
        if not job:
            error = FailureResult(error=f"Job with id {job_id} not found")
            raise web.json_response(status=404, json=to_json(error))

        job_json = to_json(job)
        return web.json_response(body=job_json)

    async def create_job(self, request: web.Request):
        body = await request.json()
        job_create = from_json(body, JobCreate)
        await self.jobs_repository.insert(job_create)
        return web.json_response()

    async def delete_job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        await self.jobs_repository.delete(job_id)
        return web.json_response()
