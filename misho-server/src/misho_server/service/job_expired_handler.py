from datetime import datetime
import logging
from misho_server.core.job import Job, JobAction, JobCreate, OnExpiryAction, Status
from misho_server.core.job.jobs_repository import JobsRepository
from misho_server.service.notification_service import NotificationService


class JobExpiredHandler:
    def __init__(self, job_repository: JobsRepository, notification_service: NotificationService):
        self._job_repository = job_repository
        self._notification_service = notification_service

    async def handle_expired_jobs(self):
        logging.info("Handling expired jobs")
        expired_jobs = await self._job_repository.list_all()
        for job in expired_jobs:
            if job.expires_at <= datetime.now():
                await self._handle_expired_job(job)

    async def _handle_expired_job(self, job: Job):
        await self._job_repository.delete(job.id)
        print(job.on_expiry_action)
        match job.on_expiry_action:
            case OnExpiryAction.CREATE_NOTIFY_JOB:
                await self._job_repository.insert(
                    JobCreate(
                        user_id=job.user.id,
                        time_slot=job.time_slot,
                        action=JobAction.NOTIFY,
                        courts_by_priority=list(job.courts_by_priority),
                        expires_at=job.time_slot.start_time(),
                        on_expiry_action=None
                    )
                )
            case None:
                pass

        msg = f"Zadatak {job.id}: {job.time_slot} za rezervaciju je istekao."
        if job.time_slot.start_time() > job.expires_at and job.status != Status.SUCCESS:
            if job.on_expiry_action == OnExpiryAction.CREATE_NOTIFY_JOB:
                msg += " Kreiran je novi zadatak za obavijest o slobodnom terminu u istom periodu."
            await self._notification_service.send_notification(job.user, msg)
