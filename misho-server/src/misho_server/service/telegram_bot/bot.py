from enum import Enum
import logging
import shlex
from misho_server.database.model import User
from misho_server.domain.user import UserId
from misho_server.domain.user_telegram_data import UserTelegramData
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepository
from misho_server.service.jobs_service import JobsService
from misho_server.service.notification_service import NotificationService
from misho_server.service.open_ai.user_client import OpenAiUserClient
from misho_server.service.signup_service import SignUpService
from misho_server.service.telegram_bot.telegram_handler import TelegramHandler
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Application


class TelegramBot:
    def __init__(
        self,
        telegram_token: str,
        handler: TelegramHandler,
        notification_service: NotificationService | None
    ):
        self._handler = handler
        self._telegram_token = telegram_token
        self._application = ApplicationBuilder().token(telegram_token).build()

        start_handler = CommandHandler('start', handler.start_handler)
        self._application.add_handler(start_handler)

        message_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, handler.message_handler)
        self._application.add_handler(message_handler)

        signup_handler = CommandHandler("signup", handler.signup_handler)
        self._application.add_handler(signup_handler)

        notification_service.subscribe(self._handle_notification)

    async def start(self):
        logging.info("Starting Telegram bot application...")
        try:
            await self._application.initialize()
            await self._application.start()
            await self._application.updater.start_polling()
        except Exception:
            await self._application.shutdown()
            raise

    async def stop(self):
        logging.info("Stopping Telegram bot application...")
        await self._application.shutdown()

    async def _handle_notification(self, user: User, message: str) -> None:
        chat_id = await self._handler.get_chat_id_for_notifications(user)
        print(chat_id)
        if chat_id is not None:
            await self._application.bot.send_message(
                chat_id=chat_id,
                text=message
            )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.stop()
