import datetime
import logging
from misho_server.config.model import ReservationMonitoringConfig
from misho_server.domain.court import CourtId
from misho_server.domain.job import Job
from misho_server.repository.available_job_reservation_slots import AvailableJobReservationSlotRepository
from misho_server.repository.jobs import JobsRepository
from misho_server.service.reservation_scheduler import ReservationScheduler


class ReservationMonitoring:
    def __init__(
        self,
        reservation_config: ReservationMonitoringConfig,
        reservation_scheduler: ReservationScheduler,
        available_job_reservation_slot_repository: AvailableJobReservationSlotRepository,
        jobs_repository: JobsRepository,
    ):
        self._config = reservation_config
        self._jobs_repository = jobs_repository
        self._reservation_scheduler = reservation_scheduler
        self._available_job_reservation_slot_repository = available_job_reservation_slot_repository

    async def run(self):
        logging.info("Running reservation monitoring")
        if self._is_new_day():
            return await self._handle_new_day()

        await self._check_for_available_job_reservation_slots()

    async def _check_for_available_job_reservation_slots(self):
        available_job_reservation_slots = await self._available_job_reservation_slot_repository.get_available_job_reservation_slots()
        logging.info(
            f"Found {len(available_job_reservation_slots)} available job reservation slots")

        jobs: dict[Job, tuple[CourtId, ...]] = {}

        for slot in available_job_reservation_slots:
            if slot.job not in jobs:
                jobs[slot.job] = tuple()
            jobs[slot.job] = jobs[slot.job] + (slot.court_id,)

        return await self._reservation_scheduler.schedule_reservations(jobs)

    async def _handle_new_day(self):
        logging.info("Handling new day")
        new_day = datetime.date.today() + datetime.timedelta(days=4)
        jobs = await self._jobs_repository.get_reservation_jobs_for_date(new_day)
        jobs_with_courts = {job: job.courts_by_priority for job in jobs}

        return await self._reservation_scheduler.schedule_reservations(jobs_with_courts)

    def _is_new_day(self):
        dt = datetime.datetime.now()
        return dt.hour == 0 and dt.minute == 0 and dt.second == 0
