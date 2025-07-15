import asyncio
from misho_server.core.reservation_calendar import CourtId
from misho_server.core.time_slot import TimeSlot
from misho_server.core.job import Job
from misho_server.service.reserve_job_executor import ReserveJobExecutor


class ReservationScheduler:
    async def schedule_reservations(self, jobs: dict[Job, tuple[CourtId, ...]]) -> None:
        raise NotImplementedError()


type CourtPool = set[CourtId]


class ReservationSchedulerImpl(ReservationScheduler):
    def __init__(self, reserve_job_executor: ReserveJobExecutor):
        self._reserve_job_executor = reserve_job_executor

    async def schedule_reservations(self, jobs: dict[Job, tuple[CourtId, ...]]) -> None:
        reserve_jobs_per_time_slot: dict[TimeSlot, list[Job]] = {}
        court_pool: dict[TimeSlot, CourtPool] = {}
        for job, courts in jobs.items():
            if job.time_slot not in reserve_jobs_per_time_slot:
                reserve_jobs_per_time_slot[job.time_slot] = []
            if job.time_slot not in court_pool:
                court_pool[job.time_slot] = set()
            reserve_jobs_per_time_slot[job.time_slot].append(job)
            court_pool[job.time_slot].update(
                courts
            )

        async def make_reserve_task(job: Job, court_pool: CourtPool):
            await self._reserve_job_executor.execute(job, court_pool)

        tasks: list[asyncio.Task[None]] = []
        for time_slot, jobs_for_time_slot in reserve_jobs_per_time_slot.items():
            court_pool_for_time_slot = court_pool[time_slot]
            for job in jobs_for_time_slot:
                task = asyncio.create_task(
                    make_reserve_task(job, court_pool_for_time_slot))
                tasks.append(task)

        await asyncio.gather(*tasks)
