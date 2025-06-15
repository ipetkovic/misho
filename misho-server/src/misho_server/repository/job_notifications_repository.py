import datetime
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine

from misho_server.domain.court import CourtId
from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.job import JobId
from misho_server.domain.job_notification import JobNotificationId, JobNotification
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.domain.time_slot import TimeSlot
import misho_server.database.model as dao
from sqlalchemy.orm import selectinload
from misho_server.repository.jobs import to_domain as job_to_domain
from misho_server.repository.time_slot import to_domain as time_to_domain


class JobNotificationsRepository:
    async def get_notifications(self) -> list[JobNotification]:
        raise NotImplementedError()

    async def update_job_notification_state(
        self,
        job_notification_state_id: JobNotificationId,
        trigger_on_available: bool
    ) -> None:
        raise NotImplementedError()


class JobNotificationsRepositorySqlite(JobNotificationsRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def get_notifications(self) -> list[JobNotification]:
        async with self._sessionmaker() as session:
            stmt = (
                select(dao.JobNotificationState.id, dao.Job, dao.JobCourt,
                       dao.ReservationCalendar.reserved_by)
                .options(
                    selectinload(dao.Job.time_slot)
                    .selectinload(dao.TimeSlot.hour_slot),
                    selectinload(dao.Job.job_courts),
                    selectinload(dao.Job.monitoring_job),
                    selectinload(dao.Job.user)
                )
                .join(dao.JobCourt, dao.Job.id == dao.JobCourt.job_id)
                .join(dao.JobNotificationState, dao.JobNotificationState.job_court_id == dao.JobCourt.id)
                .join(dao.MonitoringJob, dao.MonitoringJob.job_id == dao.Job.id)
                .join(dao.ReservationCalendar, and_(
                    dao.ReservationCalendar.time_slot_id == dao.Job.time_slot_id,
                    dao.ReservationCalendar.court_id == dao.JobCourt.court_id
                ))
                .join(dao.TimeSlot, dao.TimeSlot.id == dao.Job.time_slot_id)
                .join(dao.HourSlot, dao.TimeSlot.hour_slot_id == dao.HourSlot.id)
                .where(
                    dao.MonitoringJob.action == dao.MonitoringAction.NOTIFY,
                    or_(
                        and_(
                            dao.JobNotificationState.trigger_on_available.is_(
                                True),
                            dao.ReservationCalendar.reserved_by.is_(None),
                        ),
                        and_(
                            dao.JobNotificationState.trigger_on_available.is_(
                                False),
                            dao.ReservationCalendar.reserved_by.is_not(None),
                        ),
                    )
                )
            )

            result = await session.execute(stmt)
            rows = result.all()
            print(rows)
            notifications = [
                _to_domain(
                    job_notification_id=row[0],
                    job=row[1],
                    job_court=row[2],
                    reserved_by=row[3]
                )
                for row in rows
            ]

            return notifications

    async def update_job_notification_state(
            self,
            job_notification_state_id: JobNotificationId,
            trigger_on_available: bool
    ) -> None:
        async with self._sessionmaker() as session:
            stmt = (
                select(dao.JobNotificationState)
                .where(dao.JobNotificationState.id == job_notification_state_id)
            )
            result = await session.execute(stmt)
            job_notification_state = result.scalar_one_or_none()

            if job_notification_state is None:
                raise ValueError(
                    f"JobNotificationState with id {job_notification_state_id} not found.")

            job_notification_state.trigger_on_available = trigger_on_available
            await session.commit()


def _to_domain(job_notification_id: JobNotificationId, job: dao.Job,  job_court: dao.JobCourt, reserved_by: str | None) -> JobNotification:
    return JobNotification(
        job_notification_id=job_notification_id,
        job=job_to_domain(job),
        reservation_slot=ReservationSlot(
            court=job_court.court_id,
            time_slot=time_to_domain(job.time_slot)
        ),
        reserved_by=reserved_by
    )
