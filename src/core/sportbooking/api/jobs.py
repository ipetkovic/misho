from dataclasses import dataclass
import datetime
import json

from dataclasses_json import dataclass_json
from core.sportbooking.domain.job import Job, JobId, Status
from core.sportbooking.domain.monitoring_job import MonitoringAction
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.time_slot import TimeSlot
from core.sportbooking.repository.jobs import JobsRepository

from aiohttp import web


@dataclass
class Jobs:
    id: JobId
    time_slot: TimeSlot
    courts_by_priority: tuple[CourtId]
    action: MonitoringAction
    created_at: datetime.datetime


@dataclass_json
@dataclass
class Result:
    data: any


class JobsController:
    def __init__(self, jobs_repository: JobsRepository):
        self.jobs_repository = jobs_repository

    def register_routes(self, app: web.Application):
        app.add_routes([
            web.get('/jobs', self.jobs),
            web.get('/jobs/{job_id:\d+}', self.job),
            web.delete('/jobs/{job_id:\d+}', self.delete_job),
        ])

    async def jobs(self, _):
        jobs = await self.jobs_repository.list_all()
        jobs_json = Result(jobs).to_json()
        print(jobs_json)
        return web.json_response(body=jobs_json)

    async def job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        job = await self.jobs_repository.find_by_id(job_id)
        if not job:
            raise web.HTTPNotFound(text=f"Job with id {job_id} not found")
        return web.json_response(body=Result(job).to_json())

    async def delete_job(self, request: web.Request):
        job_id = int(request.match_info['job_id'])
        await self.jobs_repository.delete(job_id)
        return web.json_response()
