from datetime import date, timedelta
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy.orm import selectinload
import misho_server.database.model as dao
from misho_server.domain.time_slot import TimeSlot
from misho_server.repository.hour_slot import get_hour_slot, list_hour_slots
from misho_server.repository.hour_slot import to_domain as hour_slot_to_domain

type TimeSlotId = int


class TimeSlotRepositorySqlite:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def insert_time_slots(self, start_date: date, number_of_days: int) -> None:
        async with self._sessionmaker() as session:
            # 1. Get all existing hour_slot IDs
            hour_slots = await list_hour_slots(session)
            hour_slot_ids = list(hour_slots.values())

            # 2. Generate 100 future dates
            future_dates = [start_date + timedelta(days=i)
                            for i in range(number_of_days)]

            # 3. Create all combinations
            values = [
                {"date": d, "hour_slot_id": hour_slot_id}
                for d in future_dates
                for hour_slot_id in hour_slot_ids
            ]

            # 4. Insert (skip existing ones using conflict resolution)
            stmt = insert(dao.TimeSlot).values(values).on_conflict_do_nothing()

            await session.execute(stmt)
            await session.commit()


async def find_times_slots(session: AsyncSession, time_slots: list[TimeSlot]) -> dict[TimeSlot, TimeSlotId]:
    hour_slots = await list_hour_slots(session)
    pairs = [(time_slot.date, hour_slots[time_slot.hour_slot])
             for time_slot in time_slots]

    select_stmt = select(dao.TimeSlot).filter(
        tuple_(dao.TimeSlot.date, dao.TimeSlot.hour_slot_id).in_(pairs)
    ).options(selectinload(dao.TimeSlot.hour_slot))

    result = await session.execute(select_stmt)

    time_slots = result.scalars().all()

    return {TimeSlot(
        date=row.date,
        hour_slot=hour_slot_to_domain(row.hour_slot)
    ): row.id for row in time_slots}


async def find_time_slot_id(session: AsyncSession, time_slot: TimeSlot) -> TimeSlotId | None:
    result = await find_times_slots(session, time_slots=[time_slot])
    return result.get(time_slot)


def to_domain(time_slot_dao: dao.TimeSlot) -> TimeSlot:
    return TimeSlot(
        date=time_slot_dao.date,
        hour_slot=hour_slot_to_domain(time_slot_dao.hour_slot)
    )
