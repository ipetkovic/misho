import logging
from misho_server.domain.user import User
from misho_server.service.telegram_bot.common import get_username
from misho_server.service.telegram_bot.telegram_handler import ChatId, TelegramHandler
from telegram import Update
from telegram.ext import ContextTypes


class TelegramBlacklistedUserHandler(TelegramHandler):
    def __init__(self):
        pass

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)

        logging.info(
            f"Start handler called for blacklisted user: {username}")
        return None

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        logging.info(
            f"Signup handler called for blacklisted user: {username}")
        return None

    async def handle_message_notification(self, user: User) -> ChatId | None:
        return None

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        logging.info(
            f"Message handler called for blacklisted user: {username}")
        return None
