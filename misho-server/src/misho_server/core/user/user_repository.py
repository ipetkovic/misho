from misho_server.core.app_token import AppToken
from misho_server.core.user import User, UserCreate, UserId


class UserRepository:
    async def list_users(self) -> list[User]:
        raise NotImplementedError()

    async def get_user_by_id(self, user_id: UserId) -> User | None:
        raise NotImplementedError()

    async def get_user_by_username(self, username: str) -> User | None:
        raise NotImplementedError()

    async def get_user_by_auth_token(self, auth_token: str) -> User | None:
        raise NotImplementedError()

    async def create_user(self, user: UserCreate) -> tuple[User, AppToken]:
        raise NotImplementedError()
