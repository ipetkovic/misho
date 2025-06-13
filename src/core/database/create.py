from sqlalchemy.ext.asyncio import create_async_engine
from core.configs import CONFIG
from core.database.model import Base


async def create_tables(engine):
    """
    Create all tables in the database.
    This function is used to initialize the database schema.
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")
