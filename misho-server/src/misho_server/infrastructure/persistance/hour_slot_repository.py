from misho_server.core.hour_slot.hour_slot_repository import HourSlotRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
import misho_server.infrastructure.persistance.model as dao
from sqlalchemy.ext.asyncio.session import async_sessionmaker

from misho_server.core.hour_slot import HourSlot, HourSlotId


class HourSlotRepositorySqlite(HourSlotRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def list_hour_slots(self) -> list[HourSlot]:
        async with self._sessionmaker() as session:
            hour_slots = await list_hour_slots(session)
            return list(hour_slots.keys())


async def list_hour_slots(session: AsyncSession) -> dict[HourSlot, HourSlotId]:
    stmt = select(dao.HourSlot)
    result = await session.execute(stmt)
    hour_slots_dao = result.scalars().all()
    return {to_domain(hour_slot): hour_slot.id for hour_slot in hour_slots_dao}


def to_domain(hour_slot_dao: dao.HourSlot) -> HourSlot:
    return HourSlot(
        from_hour=hour_slot_dao.from_hour,
        to_hour=hour_slot_dao.to_hour
    )
