from misho_server.domain.user import User
from telegram import Update
from telegram.ext import ContextTypes


type ChatId = int


class TelegramHandler:

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()

    async def get_chat_id_for_notifications(self, user: User) -> ChatId | None:
        raise NotImplementedError()

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()
