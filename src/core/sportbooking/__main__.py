import asyncio
from datetime import date, timedelta
import datetime
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import dataclasses_json
from fastapi import FastAPI
import httpx
import core
from core.sportbooking.api.jobs import JobsController
from core.sportbooking.config import CONFIG
from core.sportbooking.database import SqliteDatabase
from core.sportbooking.database.model import Base
from core.sportbooking.domain.hour_slot import HourSlot
from core.sportbooking.domain.job import JobCreate
from core.sportbooking.domain.monitoring_job import MonitoringAction, MonitoringJobCreate
from core.sportbooking.domain.reservation_slot import ReservationSlot
from core.sportbooking.domain.reserve_job import ReserveJobCreate
from core.sportbooking.domain.session_token import SessionToken
from core.sportbooking.domain.time_slot import TimeSlot
from core.sportbooking.integration import SportBookingApiImpl
from core.sportbooking.repository.available_job_reservation_slots import AvailableJobReservationSlotRepositorySqlite
from core.sportbooking.repository.job_notifications_repository import JobNotificationsRepositorySqlite
from core.sportbooking.repository.jobs import JobsRepository, JobsRepositorySqlite
from core.sportbooking.repository.reservation_calendar import ReservationCalendarRepositorySqlite
from core.sportbooking.repository.time_slot import TimeSlotRepositorySqlite
from core.sportbooking.repository.user import UserRepositorySqlite
from core.sportbooking.repository.user_token import UserTokenRepositorySqlite
from core.sportbooking.service.job_notifier import JobNotifier
from core.sportbooking.service.mail_service import MailService
from core.sportbooking.service.reservation_monitoring import ReservationMonitoring
from core.sportbooking.service.reservation_scheduler import ReservationScheduler, ReservationSchedulerImpl
from core.sportbooking.service.reservation_service import ReservationService
from core.sportbooking.service.reserve_job_executor import ReserveJobExecutor
from core.sportbooking.service.session_token_fetch_service import SessionTokenFetchService
from sqlalchemy.ext.asyncio import create_async_engine
import core.sportbooking.api
from aiohttp import web

import logging


async def start():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    dataclasses_json.cfg.global_config.encoders[date] = date.isoformat
    dataclasses_json.cfg.global_config.decoders[date] = date.fromisoformat

    logging.getLogger("core.sportbooking").setLevel(CONFIG.logging.level)

    engine = create_async_engine(
        "sqlite+aiosqlite:///./" + CONFIG.database_path, echo=False)

    async with httpx.AsyncClient() as http_client, engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)

        sportbooking_api = SportBookingApiImpl(http_client)

        user_repository = UserRepositorySqlite(engine)

        user_token_repository = UserTokenRepositorySqlite(engine)

        jobs_repository = JobsRepositorySqlite(engine)

        time_slot_repository = TimeSlotRepositorySqlite(engine)

        reservation_calendar_repository = ReservationCalendarRepositorySqlite(
            engine)

        job_notifications_repository = JobNotificationsRepositorySqlite(
            engine)

        session_token_fetch_service = SessionTokenFetchService(
            sportbooking_api=sportbooking_api,
            user_repository=user_repository,
            user_token_repository=user_token_repository)

        mail_service = MailService(CONFIG.mailer_config)

        job_notifier = JobNotifier(
            job_notifications_repository=job_notifications_repository,
            mail_service=mail_service)

        available_job_reservation_slot_repository = AvailableJobReservationSlotRepositorySqlite(
            engine)

        reservation_service = ReservationService(
            sportbooking_api=sportbooking_api,
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
            sportbooking_api=sportbooking_api,
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

        # res = await jobs_repository.filter_by_reservation_slots(
        #     [ReservationSlot(time_slot, 8)]
        # )

        # print(res)

        # job = await jobs_repository.find_by_id(1)

        # jobs = await jobs_repository.list_all()

        # for job in jobs:
        #     await jobs_repository.delete(job.id)

        dates = (
            "2025-06-11",
            "2025-06-12"
        )

        dates = [datetime.date.fromisoformat(date) for date in dates]

        hour_slots = [
            HourSlot(from_hour=16, to_hour=17)
        ]

        # for date in dates:
        #     for hour_slot in hour_slots:
        #         await jobs_repository.insert(
        #             JobCreate(
        #                 user_id=1,
        #                 time_slot=TimeSlot(date, hour_slot),
        #                 job_type=MonitoringJobCreate(MonitoringAction.RESERVE),
        #                 courts_by_priority=[4, 5, 6, 7],
        #             )
        #         )

        # await jobs_repository.insert(
        #     JobCreate(
        #         user_id=1,
        #         time_slot=TimeSlot(datetime.date.fromisoformat(
        #             "2025-06-12"), HourSlot(from_hour=19, to_hour=21)),
        #         job_type=ReserveJobCreate(),
        #         courts_by_priority=[4, 5, 6, 7],
        #     )
        # )

        # res = await job_notifications_repository.get_notifications()
        # print(f"notifications: {res}")
        # print("stipica")
        # print(await jobs_repository.find_by_id(1))

        # await jobs_repository.delete(1)

        app = web.Application()

        JobsController(jobs_repository).register_routes(app)

        await start_http_server(app)

        await _sleep_forever()


async def start_http_server(app: web.Application):
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()


async def _sleep_forever():
    await asyncio.Event().wait()


def asyncio_run():
    asyncio.run(start())


if __name__ == "__main__":
    asyncio_run()
