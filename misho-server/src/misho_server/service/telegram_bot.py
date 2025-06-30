import logging
from misho_server.domain.user import UserId
from misho_server.domain.user_telegram_data import UserTelegramData
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepository
from misho_server.service.jobs_service import JobsService
from misho_server.service.open_ai.user_client import OpenAiUserClient
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Application

import os
from openai import OpenAI


class OpenAiUserClientBuilder:
    def __init__(self, open_ai_client: OpenAI, jobs_service: JobsService):
        self._open_ai_client = open_ai_client
        self._jobs_service = jobs_service

    def build(self, user_id: UserId) -> OpenAiUserClient:
        return OpenAiUserClient(
            open_ai_client=self._open_ai_client,
            jobs_service=self._jobs_service,
            user_id=user_id
        )


class TelegramBot:
    def __init__(
        self,
        telegram_token: str,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
        open_ai_user_client_builder: OpenAiUserClientBuilder
    ):
        self._telegram_token = telegram_token
        self._user_telegram_integration_repository = user_telegram_integration_repository
        self._open_ai_user_client_builder = open_ai_user_client_builder
        self._open_ai_clients: dict[str, OpenAiUserClient] = {}
        self._application = ApplicationBuilder().token(telegram_token).build()

        start_handler = CommandHandler('start', self._start_handler)
        self._application.add_handler(start_handler)

        message_handler = MessageHandler(
            filters.TEXT, self._message_handler)
        self._application.add_handler(message_handler)

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

    async def _start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        is_user_registered = await self._is_user_registered(update.effective_user.username)
        if not is_user_registered:
            return None

        await self._update_user_chat_id(
            username=update.effective_user.username,
            chat_id=update.effective_chat.id
        )

        message = (
            "Pozdrav! Ja sam Misho bot, "
            "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene. "
            "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija. "
            "Kako ti mogu pomoći?"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def _message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
        message = update.message.text
        open_ai_client = await self._get_open_ai_client(
            update.effective_user.username,
            update.effective_chat.id
        )

        print(update.effective_chat.id)
        print(open_ai_client)

        if open_ai_client is None:
            # TODO
            return None

        if message is None:
            return None

        response = await open_ai_client.handle_user_message(message)

        if response is not None:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

    async def _get_open_ai_client(self, username: str, chat_id: int) -> OpenAiUserClient | None:
        if username not in self._open_ai_clients:
            user_telegram_data = await self._get_user_telegram_data(username)

            if self._open_ai_clients.get(username) is None and user_telegram_data is not None:
                self._open_ai_clients[username] = self._open_ai_user_client_builder.build(
                    user_id=user_telegram_data.user.id
                )

                if user_telegram_data.chat_id != chat_id:
                    await self._update_user_chat_id(username=username, chat_id=chat_id)

        return self._open_ai_clients.get(username)

    async def _is_user_registered(self, username: str) -> bool:
        user_telegram_data = await self._get_user_telegram_data(username)
        return user_telegram_data is not None

    async def _get_user_telegram_data(self, username: str) -> UserTelegramData | None:
        return await self._user_telegram_integration_repository.get_user_telegram_data_by_username(username)

    async def _update_user_chat_id(self, username: str, chat_id: int) -> None:
        await self._user_telegram_integration_repository.update_user_telegram_chat_id(
            username=username,
            chat_id=chat_id
        )

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.stop()
