import datetime
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine

from core.sportbooking.domain.court import CourtId
from core.sportbooking.domain.hour_slot import HourSlot
from core.sportbooking.domain.job import JobId
from core.sportbooking.domain.job_notification import JobNotificationId, JobNotification
from core.sportbooking.domain.reservation_slot import ReservationSlot
from core.sportbooking.domain.time_slot import TimeSlot
import core.sportbooking.database.model as dao


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

    async def get_notifications(self):
        async with self._sessionmaker() as session:
            stmt = (
                select(dao.JobNotificationState.id, dao.Job.id, dao.JobCourt.court_id,
                       dao.TimeSlot.date, dao.HourSlot.from_hour, dao.HourSlot.to_hour, dao.ReservationCalendar.reserved_by)
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
                    # dao.MonitoringJob.action == dao.MonitoringAction.NOTIFY,
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
                    job_id=row[1],
                    court_id=row[2],
                    date=row[3],
                    from_hour=row[4],
                    to_hour=row[5],
                    reserved_by=row[6]
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


def _to_domain(job_notification_id: JobNotificationId, job_id: JobId, court_id: CourtId, date: datetime.date, from_hour: int, to_hour: int, reserved_by: str | None) -> JobNotification:
    return JobNotification(
        job_notification_id=job_notification_id,
        job_id=job_id,
        reservation_slot=ReservationSlot(
            court=court_id,
            time_slot=TimeSlot(date=date, hour_slot=HourSlot(
                from_hour=from_hour, to_hour=to_hour))
        ),
        reserved_by=reserved_by
    )
