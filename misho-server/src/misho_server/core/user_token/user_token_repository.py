from misho_server.core.session_token import SessionToken
from misho_server.core.user import UserId
from misho_server.core.user_token import UserToken


class UserTokenRepository:
    async def get_user_token(self, user_id: UserId) -> UserToken | None:
        raise NotImplementedError()

    async def set_user_token(self, user_id: UserId, token: SessionToken) -> None:
        raise NotImplementedError()
