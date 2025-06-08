import logging
from core.sportbooking.config import CONFIG
from core.sportbooking.domain.job import Job, Status
from core.sportbooking.domain.reservation_calendar import CourtId
from core.sportbooking.domain.reservation_slot import ReservationSlot
from core.sportbooking.repository.jobs import JobsRepository
from core.sportbooking.service.reservation_service import ReservationService


class ReserveJobExecutor:
    def __init__(self, job_repository: JobsRepository, reservation_service: ReservationService):
        self._job_repository = job_repository
        self._reservation_service = reservation_service

    async def execute(self, job: Job, court_pool: set[CourtId] = None):

        async def execute_reserve_job():
            return await self._execute_reserve_job(job, court_pool)

        return await execute_reserve_job()

    async def _execute_reserve_job(self, job: Job, court_pool: set[CourtId] = None):
        logging.info(f"Starting executing reserve job {job.id}")

        async def reserve() -> bool:
            # take the first court from the pool if available, go by priority
            result = None
            while result is None:
                existing = [
                    court_id
                    for court_id in job.courts_by_priority
                    if court_id in court_pool
                ]

                if not existing:
                    return False

                court_id = existing[0]
                court_pool.remove(court_id)

                try:
                    await self._reservation_service.reserve(
                        user_id=job.user_id,
                        reservation_slot=ReservationSlot(
                            job.time_slot, court_id)
                    )
                    logging.info(f"Reservation successful for job {job.id}")
                    result = True
                except Exception as e:
                    logging.error(
                        f"Reservation failed for job {job.id} with exception: {e}"
                    )

        async def update_job_status(is_success: bool):
            if CONFIG.update_job_status:
                job_status = Status.SUCCESS if is_success else Status.FAILED
                await self._job_repository.update_job_status(job.id, job_status)

        try:
            is_success = await reserve()
            await update_job_status(is_success)
            result = "succeeded" if is_success else "failed"
            logging.info(f"Job {job.id} {result}.")
        except Exception as e:
            update_job_status(False)
            print(f"Job failed with exception: {e}")
