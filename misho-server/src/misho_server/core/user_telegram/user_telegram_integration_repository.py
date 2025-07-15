from misho_server.core.user_telegram import UserTelegramData
from misho_server.core.user import UserId


class UserTelegramIntegrationRepository:
    async def get_user_telegram_data_by_username(self, username: str) -> UserTelegramData | None:
        pass

    async def get_user_telegram_data_by_user_id(self, user_id: UserId) -> UserTelegramData | None:
        pass

    async def update_user_telegram_user_id(self, username: str, user_id: int) -> None:
        pass

    async def update_user_telegram_chat_id(self, username: str, chat_id: int) -> None:
        pass
