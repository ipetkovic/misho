import datetime
import logging
from misho_server.config import CONFIG
from misho_server.config.model import ReservationMonitoringConfig
from misho_server.service.sportbooking_service import SportbookingService
from sportbooking import SportbookingApi
from misho_server.domain.reservation_calendar import ReservationCalendar
from misho_server.repository.available_job_reservation_slots import AvailableJobReservationSlotRepository
from misho_server.repository.jobs import JobsRepository
from misho_server.repository.reservation_calendar import ReservationCalendarRepository
from misho_server.repository.user import UserRepository
from misho_server.service.job_notifier import JobNotifier
from misho_server.service.reservation_scheduler import ReservationScheduler
from misho_server.service.session_token_fetch_service import SessionTokenFetchService


class ReservationMonitoring:
    def __init__(
        self,
        reservation_config: ReservationMonitoringConfig,
        sportbooking: SportbookingService,
        user_repository: UserRepository,
        reservation_calendar_repository: ReservationCalendarRepository,
        reservation_scheduler: ReservationScheduler,
        available_job_reservation_slot_repository: AvailableJobReservationSlotRepository,
        jobs_repository: JobsRepository,
        job_notifier: JobNotifier,
        token_fetch_service: SessionTokenFetchService
    ):
        self._config = reservation_config
        self._user_repository = user_repository
        self._sportbooking = sportbooking
        self._reservation_calendar_repository = reservation_calendar_repository
        self._token_fetch_service = token_fetch_service
        self._jobs_repository = jobs_repository
        self._job_notifier = job_notifier
        self._reservation_scheduler = reservation_scheduler
        self._available_job_reservation_slot_repository = available_job_reservation_slot_repository
        self._user_id = None

    async def run(self):
        if self._is_new_day():
            return await self._handle_new_day()

        logging.debug("Fetching reservation calendar")
        old_calendar = await self._reservation_calendar_repository.get_calendar()
        new_calendar = await self._get_new_calendar(old_calendar)

        diff = {}
        if old_calendar is not None:
            diff = new_calendar.diff(old_calendar)

        if old_calendar is not None and len(diff) == 0:
            logging.debug("Calendar has not changed")
        else:
            logging.debug("Calendar has changed")
            await self._reservation_calendar_repository.set_calendar(new_calendar)

        await self._check_for_available_job_reservation_slots()
        await self._job_notifier.handle()

    async def _check_for_available_job_reservation_slots(self):
        available_job_reservation_slots = await self._available_job_reservation_slot_repository.get_available_job_reservation_slots()
        logging.info(
            f"Found {len(available_job_reservation_slots)} available job reservation slots")
        jobs = {}
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

    async def _get_new_calendar(self, old_calendar: ReservationCalendar | None):
        new_calendar = await self._fetch_calendar()
        return new_calendar

    async def _fetch_calendar(self):
        user_id = await self._get_user_id()
        token = await self._token_fetch_service.get_token(user_id)
        calendar = await self._sportbooking.get_reservation_calendar(token)
        return ReservationCalendar.from_user_reservation_calendar(calendar)

    async def _get_user_id(self):
        if self._user_id is None:
            user = await self._user_repository.get_user_by_username(self._config.username)
            if user is None:
                raise ValueError(f"User {self._config.username} not found")
            self._user_id = user.id

        return self._user_id

    def _is_new_day(self):
        dt = datetime.datetime.now()
        return dt.hour == 0 and dt.minute == 0
