import datetime
import logging
from misho_server.service.sportbooking_service import SportbookingService
from misho_server.domain.session_token import SessionToken
from misho_server.repository.user import UserRepository
from misho_server.repository.user_token import UserTokenRepository


class SessionTokenFetchService:
    def __init__(
        self,
        sportbooking: SportbookingService,
        user_repository: UserRepository,
        user_token_repository: UserTokenRepository,
        refresh_after_minutes: int = 20
    ):
        self._user_repository = user_repository
        self._user_token_repository = user_token_repository
        self._sportbooking = sportbooking
        self._refresh_after_minutes = refresh_after_minutes

    async def get_token(self, user_id) -> SessionToken:
        user_token = await self._user_token_repository.get_user_token(user_id)

        if user_token is None or self._is_expired(user_token.updated_at):
            token = await self.refresh_token(user_id)
        else:
            token = user_token.token

        return token

    async def refresh_token(self, user_id) -> SessionToken:
        logging.info(f"Refreshing token for user {user_id}")
        user = await self._user_repository.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        token = await self._sportbooking.login(user.username, user.password)

        logging.debug(f"Login response for user {user_id}: {token}")

        await self._user_token_repository.set_user_token(user_id, token)

        return token

    def _is_expired(self, updated_at: datetime.datetime) -> bool:
        current_time = datetime.datetime.now()
        return (current_time - updated_at).total_seconds() > self._refresh_after_minutes * 60
