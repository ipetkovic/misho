
import datetime

from sqlalchemy import Select, Tuple, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
import core.sportbooking.database.model as dao

from core.sportbooking.domain.job import Job, JobCreate, JobId, ReserveJob, Status
from core.sportbooking.domain.monitoring_job import MonitoringAction, MonitoringJob, MonitoringJobCreate
from core.sportbooking.domain.reservation_slot import ReservationSlot
from core.sportbooking.domain.reserve_job import ReserveJobCreate
from core.sportbooking.domain.time_slot import TimeSlot
from core.sportbooking.repository.time_slot import find_time_slot_id, find_times_slots
from core.sportbooking.repository.time_slot import to_domain as time_slot_to_domain


class JobsRepository:
    async def find_by_id(self, job_id: JobId) -> Job | None:
        raise NotImplementedError()

    async def list_all(self, status: Status = None) -> list[Job]:
        raise NotImplementedError()

    async def get_reservation_jobs_for_date(self, date: datetime.date) -> list[Job]:
        raise NotImplementedError()

    async def update_job_status(self, job_id: JobId, status: Status) -> None:
        raise NotImplementedError()

    async def delete(self, job_id: JobId) -> None:
        raise NotImplementedError()


class JobsRepositorySqlite(JobsRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def insert(self, job: JobCreate) -> Job:
        async with self._sessionmaker() as session:
            time_slot_id = await find_time_slot_id(session, job.time_slot)

            job_courts = [dao.JobCourt(court_id=court_id, priority=idx)
                          for idx, court_id in enumerate(job.courts_by_priority)]

            monitoring_job = None
            action = None
            match job.job_type:
                case ReserveJobCreate():
                    action = MonitoringAction.RESERVE
                case MonitoringJobCreate(act):
                    action = act

            job_dao = dao.Job(
                user_id=job.user_id,
                time_slot_id=time_slot_id,
                job_courts=job_courts,
                monitoring_job=dao.MonitoringJob(action=action),
            )

            session.add(job_dao)

            print(job.job_type)

            await session.flush()
            for job_court in job_dao.job_courts:
                notification_state = dao.JobNotificationState(
                    job_court_id=job_court.id,
                    trigger_on_available=action == MonitoringAction.NOTIFY,
                )
                session.add(notification_state)

            await session.commit()
            await session.refresh(job_dao)

            return await self._find_by_id(session, job_dao.id)

    async def get_reservation_jobs_for_date(self, date: datetime.date) -> list[Job]:
        async with self._sessionmaker() as session:
            stmt = (
                self._select()
                .join(dao.TimeSlot, dao.Job.time_slot_id == dao.TimeSlot.id)
                .where(dao.TimeSlot.date == date)
            )
            result = await session.execute(stmt)
            jobs_dao = result.all()
            print("jure")
            print(jobs_dao)
            return [to_domain(job[0]) for job in jobs_dao]

    async def list_all(self, status: Status = None) -> list[Job]:
        async with self._sessionmaker() as session:
            stmt = self._select()

            if status is not None:
                stmt = stmt.where(dao.Job.status == status)

            result = await session.execute(stmt)
            jobs_dao = result.scalars().all()
            return [to_domain(job) for job in jobs_dao]

    async def find_by_id(self, job_id: JobId) -> Job | None:
        async with self._sessionmaker() as session:
            return await self._find_by_id(session, job_id)

    async def delete(self, job_id: JobId) -> None:
        async with self._sessionmaker() as session:
            job = await session.get(dao.Job, job_id)
            if job:
                await session.delete(job)
                await session.commit()

    async def update_job_status(self, job_id: JobId, status: Status) -> None:
        async with self._sessionmaker() as session:
            job = await session.get(dao.Job, job_id)
            if job:
                job.status = status
                await session.commit()

    async def _find_by_id(self, session: AsyncSession, job_id: JobId) -> Select:
        stmt = self._select().where(dao.Job.id == job_id)
        result = await session.execute(stmt)
        job_dao = result.scalar_one_or_none()
        print(job_dao)
        return to_domain(job_dao) if job_dao else None

    def _select(self) -> Select[Tuple]:
        return select(dao.Job).options(
            selectinload(dao.Job.time_slot)
            .selectinload(dao.TimeSlot.hour_slot),
            selectinload(dao.Job.job_courts),
            selectinload(dao.Job.monitoring_job),
        )


def to_domain(job_dao: dao.Job) -> Job:
    job_type = None
    print(job_dao.id)
    print(job_dao.monitoring_job)
    job_type = MonitoringJob(
        action=job_dao.monitoring_job.action)

    return Job(
        id=job_dao.id,
        user_id=job_dao.user_id,
        time_slot=time_slot_to_domain(job_dao.time_slot),
        job_type=job_type,
        courts_by_priority=tuple(
            court.court_id for court in job_dao.job_courts),
        created_at=job_dao.created_at,
        status=Status.PENDING,
    )
