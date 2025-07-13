import datetime
import logging
from misho_server.config.model import ReservationMonitoringConfig
from misho_server.domain.court import CourtId
from misho_server.domain.job import Job
from misho_server.service.job_expired_handler import JobExpiredHandler
from misho_server.service.reservation_calendar_sync_service import ReservationCalendarSyncService
from misho_server.repository.available_job_reservation_slots import AvailableJobReservationSlotRepository
from misho_server.repository.jobs import JobsRepository
from misho_server.service.job_notifier import JobNotifier
from misho_server.service.reservation_notification_service import ReservationNotificationService
from misho_server.service.reservation_scheduler import ReservationScheduler


class ReservationMonitoring:
    def __init__(
        self,
        reservation_config: ReservationMonitoringConfig,
        reservation_calendar_sync_service: ReservationCalendarSyncService,
        reservation_scheduler: ReservationScheduler,
        job_expired_handler: JobExpiredHandler,
        available_job_reservation_slot_repository: AvailableJobReservationSlotRepository,
        reservation_notification_service: ReservationNotificationService,
        jobs_repository: JobsRepository,
        job_notifier: JobNotifier,
    ):
        self._config = reservation_config
        self._reservation_calendar_sync_service = reservation_calendar_sync_service
        self._jobs_repository = jobs_repository
        self._job_notifier = job_notifier
        self._job_expired_handler = job_expired_handler
        self._reservation_scheduler = reservation_scheduler
        self._available_job_reservation_slot_repository = available_job_reservation_slot_repository
        self._reservation_notification_service = reservation_notification_service

    async def run(self):
        if self._is_new_day():
            return await self._handle_new_day()

        await self._reservation_calendar_sync_service.sync_calendar()
        await self._job_expired_handler.handle_expired_jobs()
        await self._check_for_available_job_reservation_slots()
        await self._job_notifier.handle()
        await self._reservation_notification_service.handle()

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
