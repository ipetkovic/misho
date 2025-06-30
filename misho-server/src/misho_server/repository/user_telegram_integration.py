

from misho_server.domain.user_telegram_data import UserTelegramData


class UserTelegramIntegrationRepository:
    async def get_user_telegram_data_by_username(self, username: str) -> UserTelegramData | None:
        pass

    async def update_user_telegram_chat_id(self, username: str, chat_id: int) -> None:
        pass
