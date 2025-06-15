
from sqlalchemy import *
from misho_server.domain.app_token import AppToken
from misho_server.domain.user import User, UserCreate, UserId
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
import secrets
import misho_server.database.model as dao


class UserRepository:
    async def get_user_by_id(self, user_id: UserId) -> User | None:
        raise NotImplementedError()

    async def get_user_by_username(self, username: str) -> User | None:
        raise NotImplementedError()

    async def get_user_by_auth_token(self, auth_token: str) -> User | None:
        raise NotImplementedError()

    async def create_user(self, user: UserCreate) -> tuple[User, AppToken]:
        raise NotImplementedError()


class UserRepositorySqlite(UserRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def create_user(self, user: UserCreate) -> tuple[User, AppToken]:
        async with self._sessionmaker() as session:
            token = secrets.token_hex(32)
            user_dao = dao.User(
                username=user.username,
                password=user.password,
                name=user.name,
                email=user.email,
                app_token=token
            )
            session.add(user_dao)
            await session.commit()
            return (_to_domain(user_dao), AppToken(token=token))

    async def get_user_by_auth_token(self, auth_token: str) -> User | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.User).where(dao.User.app_token == auth_token)
            user_dao = await session.scalar(stmt)
            return _to_domain(user_dao) if user_dao else None

    async def get_user_by_id(self, user_id: UserId) -> User | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.User).where(dao.User.id == user_id)
            user_dao = await session.scalar(stmt)
            return _to_domain(user_dao) if user_dao else None

    async def get_user_by_username(self, username: str) -> User | None:
        async with self._sessionmaker() as session:
            stmt = select(dao.User).where(dao.User.username == username)
            user_dao = await session.scalar(stmt)
            return _to_domain(user_dao) if user_dao else None


def _to_domain(user_dao: dao.User) -> User:
    return User(
        id=user_dao.id,
        username=user_dao.username,
        password=user_dao.password,
        name=user_dao.name,
        email=user_dao.email,
    )
