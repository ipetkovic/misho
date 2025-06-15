
from sqlalchemy import Select, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio.session import async_sessionmaker
import misho_server.database.model as dao

from misho_server.domain.court import Court
from misho_server.domain.hour_slot import HourSlot, HourSlotId


class CourtRepository:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def list_courts(self) -> list[Court]:
        async with self._sessionmaker() as session:
            stmt = select(dao.Court)
            result: Select[dao.Court] = await session.execute(stmt)
            courts_dao = result.scalars().all()
            return [to_domain(court) for court in courts_dao]


def to_domain(court_dao: dao.Court) -> Court:
    return Court(
        id=court_dao.id,
        name=court_dao.name,
    )
