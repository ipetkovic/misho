import logging
from misho_server.config import CONFIG
from misho_server.domain.job import Job, Status
from misho_server.domain.reservation_calendar import CourtId
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.repository.jobs import JobsRepository
from misho_server.service.mail_service import MailService
from misho_server.service.reservation_service import ReservationService


class ReserveJobExecutor:
    def __init__(
        self,
        job_repository: JobsRepository,
        reservation_service: ReservationService,
        mail_service: MailService,  # Optional, can be used for notifications
    ):
        self._job_repository = job_repository
        self._reservation_service = reservation_service
        self._mail_service = mail_service

    async def execute(self, job: Job, court_pool: set[CourtId] = None):

        async def execute_reserve_job():
            return await self._execute_reserve_job(job, court_pool)

        return await execute_reserve_job()

    async def _execute_reserve_job(self, job: Job, court_pool: set[CourtId] = None):
        logging.info(f"Starting executing reserve job {job.id}")

        async def reserve() -> ReservationSlot | None:
            # take the first court from the pool if available, go by priority
            result = None
            while result is None:
                existing = [
                    court_id
                    for court_id in job.courts_by_priority
                    if court_id in court_pool
                ]

                if not existing:
                    return None

                court_id = existing[0]
                court_pool.remove(court_id)

                try:
                    await self._reservation_service.reserve(
                        user_id=job.user.id,
                        reservation_slot=ReservationSlot(
                            time_slot=job.time_slot, court=court_id)
                    )
                    logging.info(f"Reservation successful for job {job.id}")
                    result = ReservationSlot(
                        time_slot=job.time_slot, court=court_id
                    )
                except Exception as e:
                    logging.error(
                        f"Reservation failed for job {job.id} with exception: {e}"
                    )

            return result

        reservation_slot = None
        try:
            reservation_slot = await reserve()
        except Exception as e:
            pass

        is_success = reservation_slot is not None

        result = "succeeded" if is_success else "failed"
        logging.info(f"Job {job.id} {result}.")
        await self._update_job_status(job, is_success)
        await self._notify_user(job, reservation_slot)

    async def _notify_user(self, job: Job, reservation_slot: ReservationSlot | None):
        if (reservation_slot is not None):
            body = f"Rezervacija za teren {reservation_slot.court} - {reservation_slot.time_slot} je uspješno izvršena."
        else:
            body = f"Rezervacija za termin {job.time_slot} nije uspjela."

        await self._mail_service.send_email(
            to=job.user.email,
            subject="Sportbooking obavijest",
            body=body
        )

    async def _update_job_status(self, job: Job, is_success: bool):
        if CONFIG.update_job_status:
            job_status = Status.SUCCESS if is_success else Status.FAILED
            await self._job_repository.update_job_status(job.id, job_status)
