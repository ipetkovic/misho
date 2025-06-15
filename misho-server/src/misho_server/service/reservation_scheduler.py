

import asyncio
from misho_server.domain.reservation_calendar import CourtId
from misho_server.domain.time_slot import TimeSlot
from misho_server.domain.job import Job
from misho_server.service.reserve_job_executor import ReserveJobExecutor


class ReservationScheduler:
    async def schedule_reservations(self, jobs: dict[Job, tuple[CourtId]]):
        raise NotImplementedError()


class ReservationSchedulerImpl(ReservationScheduler):
    def __init__(self, reserve_job_executor: ReserveJobExecutor):
        self._reserve_job_executor = reserve_job_executor

    async def schedule_reservations(self, jobs: dict[Job, tuple[CourtId]]):
        reserve_jobs_per_time_slot: dict[TimeSlot, list[Job]] = {}
        court_pool: dict[TimeSlot, set[CourtId]] = {}
        for job, courts in jobs.items():
            if job.time_slot not in reserve_jobs_per_time_slot:
                reserve_jobs_per_time_slot[job.time_slot] = []
            if job.time_slot not in court_pool:
                court_pool[job.time_slot] = set()
            reserve_jobs_per_time_slot[job.time_slot].append(job)
            court_pool[job.time_slot].update(
                courts
            )

        async def make_reserve_task(job, court_pool):
            return await self._reserve_job_executor.execute(job, court_pool)

        tasks = []
        for time_slot, jobs in reserve_jobs_per_time_slot.items():
            court_pool_for_time_slot = court_pool[time_slot]
            for job in jobs:
                task = asyncio.create_task(
                    make_reserve_task(job, court_pool_for_time_slot))
                tasks.append(task)

        return await asyncio.gather(*tasks)
