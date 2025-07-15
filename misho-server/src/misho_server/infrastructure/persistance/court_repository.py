from misho_server.core.court.court_repository import CourtRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
import misho_server.infrastructure.persistance.model as dao
from misho_server.core.court import Court


class CourtRepositorySqlite(CourtRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def list_courts(self) -> list[Court]:
        async with self._sessionmaker() as session:
            stmt = select(dao.Court)
            result = await session.execute(stmt)
            courts_dao = result.scalars().all()
            return [to_domain(court) for court in courts_dao]


def to_domain(court_dao: dao.Court) -> Court:
    return Court(
        id=court_dao.id,
        name=court_dao.name,
    )
