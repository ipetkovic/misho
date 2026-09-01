
import datetime
from typing import Tuple

from misho_server.core.job.jobs_repository import JobsRepository
from sqlalchemy.sql import Select, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
import misho_server.infrastructure.persistance.model as dao

from misho_server.core.job import Job, JobAction, JobCreate, JobId, Status
from misho_server.core.user import UserId
from misho_server.infrastructure.persistance.user_repository import to_domain as user_to_domain
from misho_server.core.time_slot import TimeSlot
from misho_server.infrastructure.persistance.time_slot_repository import find_time_slot_id
from misho_server.infrastructure.persistance.time_slot_repository import to_domain as time_slot_to_domain


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
                monitoring_job=dao.MonitoringJob(action=job.action),
                expires_at=job.expires_at,
                on_expiry_action=job.on_expiry_action
            )

            session.add(job_dao)

            await session.flush()
            for job_court in job_dao.job_courts:
                notification_state = dao.JobNotificationState(
                    job_court_id=job_court.id,
                    trigger_on_available=job.action == JobAction.NOTIFY,
                )
                session.add(notification_state)

            await session.commit()
            await session.refresh(job_dao)

            job_created = await self._find_by_id(session, job_dao.id)

            if job_created is None:
                raise ValueError(
                    f"Job with ID {job_dao.id} not found after insertion.")

            return job_created

    async def get_reservation_jobs_for_date(self, date: datetime.date) -> list[Job]:
        async with self._sessionmaker() as session:
            stmt = (
                self._select()
                .join(dao.TimeSlot, dao.Job.time_slot_id == dao.TimeSlot.id)
                .where(dao.TimeSlot.date == date)
            )
            result = await session.execute(stmt)
            jobs_dao = result.all()
            return [to_domain(job[0]) for job in jobs_dao]

    async def list_all(self, statuses: list[Status] | None = None, user_id: UserId | None = None) -> list[Job]:
        async with self._sessionmaker() as session:
            stmt = self._select()

            if statuses is not None:
                stmt = stmt.where(dao.Job.status.in_(statuses))

            if user_id is not None:
                stmt = stmt.where(dao.Job.user_id == user_id)

            result = await session.execute(stmt)
            jobs_dao = result.scalars().all()
            return [to_domain(job) for job in jobs_dao]

    async def find_by_id(self, job_id: JobId) -> Job | None:
        async with self._sessionmaker() as session:
            return await self._find_by_id(session, job_id)

    async def find_by_time_slot(self, time_slot: TimeSlot, user_id: UserId | None = None) -> Job | None:
        async with self._sessionmaker() as session:
            time_slot_id = await find_time_slot_id(session, time_slot)
            stmt = self._select().where(dao.Job.time_slot_id == time_slot_id)
            if user_id is not None:
                stmt = stmt.where(dao.Job.user_id == user_id)
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

    async def _find_by_id(self, session: AsyncSession, job_id: JobId) -> Job | None:
        stmt = self._select().where(dao.Job.id == job_id)
        result = await session.execute(stmt)
        job_dao = result.scalar_one_or_none()
        return to_domain(job_dao) if job_dao else None

    def _select(self) -> Select[Tuple[dao.Job]]:
        return select(dao.Job).options(
            selectinload(dao.Job.time_slot)
            .selectinload(dao.TimeSlot.hour_slot),
            selectinload(dao.Job.job_courts),
            selectinload(dao.Job.monitoring_job),
            selectinload(dao.Job.user)
        )


def to_domain(job_dao: dao.Job) -> Job:
    expires_at = job_dao.expires_at
    time_slot = time_slot_to_domain(job_dao.time_slot)
    if expires_at is None:
        expires_at = time_slot.start_time()

    if job_dao.monitoring_job is None:
        action = JobAction.RESERVE  # TODO: fix
    else:
        action = job_dao.monitoring_job.action

    return Job(
        id=job_dao.id,
        user=user_to_domain(job_dao.user),
        time_slot=time_slot,
        action=action,
        courts_by_priority=tuple(
            court.court_id for court in job_dao.job_courts),
        created_at=job_dao.created_at,
        status=job_dao.status,
        expires_at=expires_at,
        on_expiry_action=job_dao.on_expiry_action
    )
