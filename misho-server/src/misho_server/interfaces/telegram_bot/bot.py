import logging
from misho_server.core.user import User
from misho_server.interfaces.telegram_bot import TelegramBot
from misho_server.interfaces.telegram_bot.common import get_chat_id
from misho_server.interfaces.telegram_bot.telegram_handler import TelegramHandler
from misho_server.service.notification_service import NotificationService
from telegram import Update
from telegram.ext import filters, ContextTypes, MessageHandler, ApplicationBuilder, CommandHandler


class TelegramBotImpl(TelegramBot):
    def __init__(
        self,
        telegram_token: str,
        handler: TelegramHandler,
        notification_service: NotificationService
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

        self._application.add_error_handler(self._error_handler)  # type: ignore

        notification_service.subscribe(self._handle_notification)

    async def start(self):
        logging.info("Starting Telegram bot application...")
        try:
            await self._application.initialize()
            await self._application.start()
            if self._application.updater is None:
                raise RuntimeError("Updater is not initialized.")
            await self._application.updater.start_polling()
        except Exception:
            await self._application.shutdown()
            raise

    async def stop(self):
        logging.info("Stopping Telegram bot application...")
        await self._application.shutdown()

    async def _handle_notification(self, user: User, message: str) -> None:
        chat_id = await self._handler.handle_message_notification(user, message)
        if chat_id is not None:
            await self._application.bot.send_message(
                chat_id=chat_id,
                text=message
            )

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Catch anything an update handler raises.

        Without this, python-telegram-bot only logs "No error handlers are
        registered" and the user is left with silence, which is
        indistinguishable from the bot being down.
        """
        logging.error("Unhandled exception while processing update",
                      exc_info=context.error)

        if not isinstance(update, Update):
            return

        chat_id = get_chat_id(update)
        if chat_id is None:
            return

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Došlo je do greške. Pokušaj ponovno za koji trenutak."
            )
        except Exception:
            # An error handler that raises is swallowed, putting us back to
            # silence -- so this must never propagate.
            logging.exception(
                "Failed to deliver error message to chat %s", chat_id)
