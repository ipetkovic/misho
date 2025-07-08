

from datetime import datetime
from misho_server.domain.job import Status
from misho_server.repository.jobs import JobsRepository
from misho_server.service.job_expired_service import JobExpiredHandler


class JobExpiredMonitoringService:
    def __init__(self, job_repository: JobsRepository, job_expired_handler: JobExpiredHandler):
        self._job_repository = job_repository
        self._job_expired_handler = job_expired_handler

    async def monitor_for_expired_jobs(self):
        expired_jobs = await self._job_repository.list_all()
        for job in expired_jobs:
            if job.expires_at <= datetime.now():
                await self._job_expired_handler.handle_expired_job(job)
