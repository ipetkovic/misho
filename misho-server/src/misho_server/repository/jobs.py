
import datetime

from sqlalchemy import Select, Tuple, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
import misho_server.database.model as dao

from misho_server.domain.job import Job, JobCreate, JobId, Status
from misho_server.domain.user import UserId
from misho_server.repository.user import _to_domain as user_to_domain
from misho_server.domain.monitoring_job import MonitoringAction, MonitoringJob, MonitoringJobCreate
from misho_server.domain.time_slot import TimeSlot
from misho_server.repository.time_slot import find_time_slot_id
from misho_server.repository.time_slot import to_domain as time_slot_to_domain


class JobsRepository:
    async def insert(self, job: JobCreate) -> Job:
        raise NotImplementedError()

    async def find_by_id(self, job_id: JobId) -> Job | None:
        raise NotImplementedError()

    async def find_by_time_slot(
        self, time_slot: TimeSlot
    ) -> Job | None:
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

            job_dao = dao.Job(
                user_id=job.user_id,
                time_slot_id=time_slot_id,
                job_courts=job_courts,
                monitoring_job=dao.MonitoringJob(action=job.job_type.action),
            )

            session.add(job_dao)

            print(job.job_type)

            await session.flush()
            for job_court in job_dao.job_courts:
                notification_state = dao.JobNotificationState(
                    job_court_id=job_court.id,
                    trigger_on_available=job.job_type.action == MonitoringAction.NOTIFY,
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

    async def list_all(self, status: Status = None, user_id: UserId = None) -> list[Job]:
        async with self._sessionmaker() as session:
            stmt = self._select()

            if status is not None:
                stmt = stmt.where(dao.Job.status == status)

            if user_id is not None:
                stmt = stmt.where(dao.Job.user_id == user_id)

            result = await session.execute(stmt)
            jobs_dao = result.scalars().all()
            return [to_domain(job) for job in jobs_dao]

    async def find_by_id(self, job_id: JobId) -> Job | None:
        async with self._sessionmaker() as session:
            return await self._find_by_id(session, job_id)

    async def find_by_time_slot(self, time_slot: TimeSlot) -> Job | None:
        async with self._sessionmaker() as session:
            time_slot_id = await find_time_slot_id(session, time_slot)
            stmt = self._select().where(dao.Job.time_slot_id == time_slot_id)
            result = await session.execute(stmt)
            job_dao = result.scalar_one_or_none()
            return to_domain(job_dao) if job_dao else None

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
            selectinload(dao.Job.user)
        )


def to_domain(job_dao: dao.Job) -> Job:
    job_type = None
    print(job_dao.id)
    print(job_dao.monitoring_job)
    job_type = MonitoringJob(
        action=job_dao.monitoring_job.action)

    return Job(
        id=job_dao.id,
        user=user_to_domain(job_dao.user),
        time_slot=time_slot_to_domain(job_dao.time_slot),
        job_type=job_type,
        courts_by_priority=tuple(
            court.court_id for court in job_dao.job_courts),
        created_at=job_dao.created_at,
        status=job_dao.status
    )
