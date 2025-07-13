import asyncio
from datetime import timedelta
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from misho_server.controller.reservation_calendar import ReservationCalendarController
from misho_server.http.auth import AuthMiddleware
from misho_server.http.http_app import HttpApplication
from misho_server.controller.jobs import JobsController
from misho_server.controller.signup import SignUpController
from apscheduler.triggers.cron import CronTrigger
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
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepositorySqlite
from misho_server.repository.user_token import UserTokenRepositorySqlite
from misho_server.service.job_expired_handler import JobExpiredHandler
from misho_server.service.job_notifier import JobNotifier
from misho_server.service.jobs_service import JobsService
from misho_server.service.notification_service import NotificationService
from misho_server.service.open_ai.tool_handler import OpenAiToolHandler
from misho_server.service.reservation_calendar import ReservationCalendarService
from misho_server.service.reservation_calendar_sync_service import ReservationCalendarSyncService
from misho_server.service.reservation_cancel_service import ReservationCancelService
from misho_server.service.reservation_monitoring import ReservationMonitoring
from misho_server.service.reservation_notification_service import ReservationNotificationService
from misho_server.service.reservation_scheduler import ReservationSchedulerImpl
from misho_server.service.reservation_service import ReservationService
from misho_server.service.reserve_job_executor import ReserveJobExecutor
from misho_server.service.session_token_fetch_service import SessionTokenFetchService
from misho_server.service.signup_service import SignUpService
from misho_server.service.telegram_bot.blacklisted_handler import TelegramBlacklistedUserHandler
from misho_server.service.telegram_bot.bot import TelegramBot
from misho_server.service.telegram_bot.onboarding_handler import TelegramOnboardingHandler
from misho_server.service.telegram_bot.standard_handler import OpenAiUserClientBuilder, TelegramStandardHandler
from misho_server.service.telegram_bot.telegram_handler_delegator import TelegramHandlerDelegator
from openai import OpenAI
from sqlalchemy.ext.asyncio import create_async_engine

import logging

from misho_server.service.sportbooking_service import SportbookingServiceImpl
import sportbooking


async def start():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logging.getLogger("core").setLevel(CONFIG.logging.level)

    print(CONFIG.database_path)

    engine = create_async_engine(
        "sqlite+aiosqlite:///./" + CONFIG.database_path, echo=False)

    async with sportbooking.SportbookingApi() as sportbooking_api, engine.begin():
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

        notification_service = NotificationService()

        job_notifier = JobNotifier(
            job_notifications_repository=job_notifications_repository,
            notification_service=notification_service)

        available_job_reservation_slot_repository = AvailableJobReservationSlotRepositorySqlite(
            engine)

        reservation_service = ReservationService(
            sportbooking=sportbooking_service,
            session_token_fetch_service=session_token_fetch_service)

        reserve_job_executor = ReserveJobExecutor(
            job_repository=jobs_repository,
            reservation_service=reservation_service,
            notification_service=notification_service
        )

        reservation_scheduler = ReservationSchedulerImpl(
            reserve_job_executor=reserve_job_executor)

        reservation_calendar_sync_service = ReservationCalendarSyncService(
            reservation_calendar_repository=reservation_calendar_repository,
            user_repository=user_repository,
            token_fetch_service=session_token_fetch_service,
            sporbooking_service=sportbooking_service
        )

        job_expired_handler = JobExpiredHandler(
            job_repository=jobs_repository,
            notification_service=notification_service,
        )

        reservation_calendar_service = ReservationCalendarService(
            reservation_calendar_repository=reservation_calendar_repository,
            user_repository=user_repository,
        )

        reservation_notification_service = ReservationNotificationService(
            reservation_calendar_service=reservation_calendar_service,
            user_repository=user_repository,
            notification_service=notification_service,
        )

        reservation_monitoring = ReservationMonitoring(
            reservation_config=CONFIG.reservation_monitoring,  # Replace with actual config
            jobs_repository=jobs_repository,
            reservation_scheduler=reservation_scheduler,
            available_job_reservation_slot_repository=available_job_reservation_slot_repository,
        )

        await time_slot_repository.insert_time_slots(datetime.date.today() - timedelta(days=10),
                                                     number_of_days=100)

        scheduler = AsyncIOScheduler()
        scheduler.add_job(reservation_monitoring.run,  # type: ignore
                          name="reservation_monitoring",
                          trigger=CONFIG.reservation_monitoring.cron)
        scheduler.add_job(  # type: ignore
            reservation_calendar_sync_service.sync_calendar,
            name="reservation_calendar_sync",
            trigger=CronTrigger(hour='*', minute='*', second='25,55')
        )
        scheduler.add_job(  # type: ignore
            job_expired_handler.handle_expired_jobs,
            name="job_expired_handler",
            trigger=CronTrigger(hour='*', minute='*', second='0')
        )
        scheduler.add_job(  # type: ignore
            job_notifier.handle,
            name="job_notifier",
            trigger=CronTrigger(hour='*', minute='*', second='0,30')
        )
        scheduler.add_job(  # type: ignore
            reservation_notification_service.handle,
            name="reservation_notification_service",
            trigger=CronTrigger(hour='*', minute='*', second='0')
        )
        scheduler.start()

        hour_slot_repository = HourSlotRepository(engine)
        court_respository = CourtRepository(engine)

        jobs_service = JobsService(jobs_repository=jobs_repository,
                                   hour_slots_repository=hour_slot_repository,
                                   job_create_config=CONFIG.job_create_config,
                                   court_repository=court_respository)

        jobs_controller = JobsController(
            jobs_service=jobs_service,
        )
        signup_controller = SignUpController(
            user_service=user_repository, sportbooking=sportbooking_service)

        auth = AuthMiddleware(user_repository=user_repository)
        http_app = HttpApplication(auth)

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

        user_telegram_integration_repository = UserTelegramIntegrationRepositorySqlite(
            engine=engine)

        signup_service = SignUpService(user_service=user_repository,
                                       sportbooking=sportbooking_service
                                       )

        reservation_cancel_service = ReservationCancelService(
            sportbooking=sportbooking_service,
            session_token_fetch_service=session_token_fetch_service
        )

        open_ai_tool_handler = OpenAiToolHandler(
            jobs_service=jobs_service,
            reservation_service=reservation_service,
            reservation_cancel_service=reservation_cancel_service,
            reservation_calendar_service=reservation_calendar_service
        )

        open_ai_user_client_builder = OpenAiUserClientBuilder(
            open_ai_client=OpenAI(),
            open_ai_tool_handler=open_ai_tool_handler
        )

        telegram_blacklisted_handler = TelegramBlacklistedUserHandler()
        telegram_onboarding_handler = TelegramOnboardingHandler(
            user_telegram_integration_repository=user_telegram_integration_repository,
            signup_service=signup_service,
        )
        telegram_standard_handler = TelegramStandardHandler(
            user_telegram_integration_repository=user_telegram_integration_repository,
            open_ai_user_client_builder=open_ai_user_client_builder,
        )

        telegram_handler_delegator = TelegramHandlerDelegator(
            user_telegram_integration_repository=user_telegram_integration_repository,
            blacklisted_handler=telegram_blacklisted_handler,
            onboarding_handler=telegram_onboarding_handler,
            standard_handler=telegram_standard_handler
        )

        async with TelegramBot(
            telegram_token=CONFIG.telegram_bot_token,
            handler=telegram_handler_delegator,
            notification_service=notification_service
        ):
            await _sleep_forever()


async def _sleep_forever():
    await asyncio.Event().wait()


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
