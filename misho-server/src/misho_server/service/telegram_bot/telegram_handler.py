from misho_server.domain.user import User
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Application


type ChatId = int


class TelegramHandler:

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        raise NotImplementedError()

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        raise NotImplementedError()

    async def handle_notification(self, user: User) -> ChatId | None:
        raise NotImplementedError()

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        raise NotImplementedError()
