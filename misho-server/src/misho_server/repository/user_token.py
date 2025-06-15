import datetime

from sqlalchemy import Engine, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session
from misho_server.database import SqliteDatabase, SqliteDatabaseConnection
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from misho_server.domain.session_token import SessionToken
from misho_server.domain.user import UserId
from misho_server.domain.user_token import UserToken
import misho_server.database.model as dao


class UserTokenRepository:
    async def get_user_token(self, user_id) -> UserToken | None:
        raise NotImplementedError()

    async def set_user_token(self, user_id: UserId, token: SessionToken) -> None:
        raise NotImplementedError()


class UserTokenRepositorySqlite(UserTokenRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def get_user_token(self, user_id: UserId) -> UserToken | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.UserToken).where(
                dao.UserToken.user_id == user_id)
            user_token = await session.scalar(stmt)
            return _to_domain(user_token) if user_token else None

    async def set_user_token(self, user_id: UserId, token: SessionToken) -> None:
        async with self._sessionmaker() as session:
            print(
                f"Setting user token for user_id={user_id}, {token}")

            stmt = insert(dao.UserToken).values(
                user_id=user_id,
                token=token.value,
            ).on_conflict_do_update(
                index_elements=[dao.UserToken.user_id],
                set_=dict(
                    token=token.value,
                    updated_at=datetime.datetime.now()
                )
            )

            await session.execute(stmt)
            await session.commit()


def _to_domain(user_token_dao=dao.UserToken) -> UserToken:
    return UserToken(
        token=SessionToken(value=user_token_dao.token),
        updated_at=user_token_dao.updated_at
    )
