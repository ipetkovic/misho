from datetime import datetime, time
from misho_server.domain.job import Job, JobCreate, OnExpiryAction, Status
from misho_server.repository.jobs import JobsRepository
from misho_server.service.notification_service import NotificationService


class JobExpiredHandler:
    def __init__(self, job_repository: JobsRepository, notification_service: NotificationService):
        self._job_repository = job_repository
        self._notification_service = notification_service

    async def handle_expired_job(self, job: Job) -> None:
        match job.on_expiry_action:
            case OnExpiryAction.CREATE_NOTIFY_JOB:
                expires_at = self._get_job_start_time(job)

                await self._job_repository.insert(
                    JobCreate(
                        user_id=job.user.id,
                        time_slot=job.time_slot,
                        action=job.action,
                        courts_by_priority=list(job.courts_by_priority),
                        expires_at=expires_at,
                        on_expiry_action=None  # No further action needed for this job
                    )
                )
            case None:
                pass

        await self._job_repository.delete(job.id)

        msg = f"Zadatak {job.id}: {job.time_slot} za rezervaciju je istekao."
        if self._get_job_start_time(job) > job.expires_at and job.status != Status.SUCCESS:
            if job.on_expiry_action == OnExpiryAction.CREATE_NOTIFY_JOB:
                msg += " Kreiran je novi zadatak za obavijest o slobodnom terminu u istom periodu."
            await self._notification_service.send_notification(job.user, msg)

    def _get_job_start_time(self, job: Job) -> datetime:
        return datetime.combine(job.time_slot.date, time(
            hour=job.time_slot.hour_slot.from_hour))
