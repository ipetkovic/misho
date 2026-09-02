from misho_server.core.user_telegram import UserTelegramData

from misho_server.infrastructure.persistance.user_repository import to_domain as user_to_domain
from misho_server.core.user_telegram.user_telegram_integration_repository import UserTelegramIntegrationRepository
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from misho_server.core.user import UserId
import misho_server.infrastructure.persistance.model as dao


class UserTelegramIntegrationRepositorySqlite(UserTelegramIntegrationRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def get_user_telegram_data_by_username(self, username: str) -> UserTelegramData | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.UserTelegramIntegration).options(
                selectinload(dao.UserTelegramIntegration.user)
            ).where(dao.UserTelegramIntegration.username == username)
            user_telegram_data = await session.scalar(stmt)
            return _to_domain(user_telegram_data) if user_telegram_data else None

    async def get_user_telegram_data_by_user_id(self, user_id: UserId) -> UserTelegramData | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.UserTelegramIntegration).options(
                selectinload(dao.UserTelegramIntegration.user)
            ).where(dao.UserTelegramIntegration.user_id == user_id)
            user_telegram_data = await session.scalar(stmt)
            return _to_domain(user_telegram_data) if user_telegram_data else None

    async def create_user_telegram_data(self, username: str) -> None:
        async with self._sessionmaker() as session:
            session.add(dao.UserTelegramIntegration(username=username))
            await session.commit()

    async def update_user_telegram_user_id(self, username: str, user_id: int) -> None:
        async with self._sessionmaker() as session:
            stmt = update(dao.UserTelegramIntegration).where(
                dao.UserTelegramIntegration.username == username
            ).values(user_id=user_id)

            result = await session.execute(stmt)
            if result.rowcount == 0:
                # Silently updating nothing is how a signup came to report
                # success while leaving the user stuck in onboarding.
                raise ValueError(
                    f"No Telegram integration row for username: {username}")
            await session.commit()

    async def update_user_telegram_chat_id(self, username: str, chat_id: int) -> None:
        async with self._sessionmaker() as session:
            stmt = update(dao.UserTelegramIntegration).where(
                dao.UserTelegramIntegration.username == username
            ).values(chat_id=chat_id)

            await session.execute(stmt)
            await session.commit()


def _to_domain(user_telegram_data_dao: dao.UserTelegramIntegration) -> UserTelegramData:
    return UserTelegramData(
        user=user_to_domain(
            user_telegram_data_dao.user) if user_telegram_data_dao.user else None,
        chat_id=user_telegram_data_dao.chat_id,
        username=user_telegram_data_dao.username,
        enable_notifications=user_telegram_data_dao.enable_notifications,
        created_at=user_telegram_data_dao.created_at,
        updated_at=user_telegram_data_dao.updated_at,
    )
