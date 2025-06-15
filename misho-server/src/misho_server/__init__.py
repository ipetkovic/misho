import asyncio
from datetime import timedelta
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from misho_server.controller.reservation_calendar import ReservationCalendarController
from misho_server.http.auth import AuthMiddleware
from misho_server.http.http_app import HttpApplication
from misho_server.controller.jobs import JobsController
from misho_server.controller.signup import SignUpController
from misho_server.config import CONFIG
from misho_server.database.migration import migrate
from misho_server.repository.available_job_reservation_slots import AvailableJobReservationSlotRepositorySqlite
from misho_server.repository.court import CourtRepository
from misho_server.repository.hour_slot import HourSlotRepository
from misho_server.repository.job_notifications_repository import JobNotificationsRepositorySqlite
from misho_server.repository.jobs import JobsRepositorySqlite
from misho_server.repository.reservation_calendar import ReservationCalendarRepositorySqlite
from misho_server.repository.time_slot import TimeSlotRepositorySqlite
from misho_server.repository.user import UserRepositorySqlite
from misho_server.repository.user_token import UserTokenRepositorySqlite
from misho_server.service.job_notifier import JobNotifier
from misho_server.service.mail_service import MailService
from misho_server.service.reservation_monitoring import ReservationMonitoring
from misho_server.service.reservation_scheduler import ReservationSchedulerImpl
from misho_server.service.reservation_service import ReservationService
from misho_server.service.reserve_job_executor import ReserveJobExecutor
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from sqlalchemy.ext.asyncio import create_async_engine
from aiohttp import web

import logging

from misho_server.service.sportbooking_service import SportbookingServiceImpl
import sportbooking


async def start():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logging.getLogger("core").setLevel(CONFIG.logging.level)

    engine = create_async_engine(
        "sqlite+aiosqlite:///./" + CONFIG.database_path, echo=False)

    async with sportbooking.SportbookingApi() as sportbooking_api, engine.begin() as conn:
        migrate()

        sportbooking_service = SportbookingServiceImpl(
            sportbooking_api=sportbooking_api)

        user_repository = UserRepositorySqlite(engine)

        user_token_repository = UserTokenRepositorySqlite(engine)

        jobs_repository = JobsRepositorySqlite(engine)

        time_slot_repository = TimeSlotRepositorySqlite(engine)

        reservation_calendar_repository = ReservationCalendarRepositorySqlite(
            engine)

        job_notifications_repository = JobNotificationsRepositorySqlite(
            engine)

        session_token_fetch_service = SessionTokenFetchService(
            sportbooking=sportbooking_service,
            user_repository=user_repository,
            user_token_repository=user_token_repository)

        mail_service = MailService(CONFIG.mailer_config)

        job_notifier = JobNotifier(
            job_notifications_repository=job_notifications_repository,
            mail_service=mail_service)

        available_job_reservation_slot_repository = AvailableJobReservationSlotRepositorySqlite(
            engine)

        reservation_service = ReservationService(
            sportbooking=sportbooking_service,
            session_token_fetch_service=session_token_fetch_service)

        reserve_job_executor = ReserveJobExecutor(
            job_repository=jobs_repository,
            reservation_service=reservation_service,
            mail_service=mail_service,
        )

        reservation_scheduler = ReservationSchedulerImpl(
            reserve_job_executor=reserve_job_executor)

        reservation_monitoring = ReservationMonitoring(
            reservation_config=CONFIG.reservation_monitoring,  # Replace with actual config
            sportbooking=sportbooking_service,
            user_repository=user_repository,
            reservation_calendar_repository=reservation_calendar_repository,
            jobs_repository=jobs_repository,
            job_notifier=job_notifier,
            reservation_scheduler=reservation_scheduler,
            available_job_reservation_slot_repository=available_job_reservation_slot_repository,
            token_fetch_service=session_token_fetch_service
        )

        await time_slot_repository.insert_time_slots(datetime.date.today() - timedelta(days=10),
                                                     number_of_days=100)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(reservation_monitoring.run,
                          trigger=CONFIG.reservation_monitoring.cron)
        scheduler.start()

        hour_slot_repository = HourSlotRepository(engine)
        court_respository = CourtRepository(engine)

        jobs_controller = JobsController(
            jobs_repository=jobs_repository,
            hour_slots_repository=hour_slot_repository,
            court_repository=court_respository
        )
        signup_controller = SignUpController(
            user_service=user_repository, sportbooking=sportbooking_service)

        auth = AuthMiddleware(user_repository=user_repository)
        http_app = HttpApplication(auth)
        app = web.Application(middlewares=[auth.middleware])

        reservation_calendar_controller = ReservationCalendarController(
            sportbooking=sportbooking_service, session_token_fetch_service=session_token_fetch_service)

        http_app.add_routes(
            jobs_controller.get_routes()
        ).add_routes(
            signup_controller.get_routes()
        ).add_routes(
            reservation_calendar_controller.get_routes()
        )

        await http_app.start_server()
        logging.info("HTTP server started")

        await _sleep_forever()


async def _sleep_forever():
    await asyncio.Event().wait()


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
