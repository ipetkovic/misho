from dataclasses import dataclass

from sqlalchemy.orm import selectinload

from dataclasses import dataclass
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from misho_server.domain.court import CourtId
import misho_server.database.model as dao
from misho_server.domain.job import Job
from misho_server.repository import jobs


@dataclass(frozen=True)
class AvailableJobReservationSlot:
    job: Job
    court_id: CourtId


class AvailableJobReservationSlotRepository:
    async def get_available_job_reservation_slots() -> list[AvailableJobReservationSlot]:
        raise NotImplementedError()


class AvailableJobReservationSlotRepositorySqlite(AvailableJobReservationSlot):
    def __init__(self, engine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def get_available_job_reservation_slots(self) -> list[AvailableJobReservationSlot]:
        async with self._sessionmaker() as session:
            stmt = (
                select(dao.Job, dao.JobCourt.court_id).options(
                    selectinload(dao.Job.time_slot)
                    .selectinload(dao.TimeSlot.hour_slot),
                    selectinload(dao.Job.job_courts),
                    selectinload(dao.Job.monitoring_job),
                    selectinload(dao.Job.user),
                )
                .join(dao.JobCourt, dao.Job.id == dao.JobCourt.job_id)
                .join(dao.MonitoringJob, dao.MonitoringJob.job_id == dao.Job.id)
                .join(dao.ReservationCalendar, and_(
                    dao.ReservationCalendar.time_slot_id == dao.Job.time_slot_id,
                    dao.ReservationCalendar.court_id == dao.JobCourt.court_id
                ))
                .join(dao.TimeSlot, dao.TimeSlot.id == dao.Job.time_slot_id)
                .join(dao.HourSlot, dao.TimeSlot.hour_slot_id == dao.HourSlot.id)
                .where(
                    and_(
                        dao.MonitoringJob.action == dao.MonitoringAction.RESERVE,
                        dao.ReservationCalendar.reserved_by == None,
                        dao.Job.status == dao.Status.PENDING,
                    )
                )
            )

            result = await session.execute(stmt)
            rows = result.all()
            print(rows)
            return [AvailableJobReservationSlot(
                jobs.to_domain(row[0]), row[1]) for row in rows]
