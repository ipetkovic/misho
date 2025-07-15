from misho_server.core.user import User
from telegram import Update
from telegram.ext import ContextTypes


type ChatId = int


class TelegramHandler:

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()

    async def handle_message_notification(self, user: User, message: str) -> ChatId | None:
        raise NotImplementedError()

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        raise NotImplementedError()
