from misho_server.domain.user import User, UserId
from misho_server.domain.user_telegram_data import UserTelegramData
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepository
from misho_server.service.jobs_service import JobsService
from misho_server.service.open_ai.user_client import OpenAiUserClient
from misho_server.service.telegram_bot.telegram_handler import ChatId
from openai import OpenAI
from telegram import Update
from telegram.ext import ContextTypes


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


class TelegramStandardHandler:
    def __init__(
        self,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
        open_ai_user_client_builder: OpenAiUserClientBuilder,
    ):
        self._open_ai_user_client_builder = open_ai_user_client_builder
        self._open_ai_clients: dict[str, OpenAiUserClient] = {}
        self._user_telegram_integration_repository = user_telegram_integration_repository

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = (
            "Pozdrav! Ja sam Misho bot, "
            "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene.\n"
            "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija.\n"
        )

        await self._update_user_chat_id(
            username=update.effective_user.username,
            chat_id=update.effective_chat.id
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return None

    async def get_chat_id_for_notifications(self, user: User) -> ChatId | None:
        user_telegram_data = await self._get_user_telegram_data_by_user_id(user.id)
        return user_telegram_data.chat_id

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message.text
        open_ai_client = await self._get_open_ai_client(
            update.effective_user.username
        )

        if message is None:
            return None

        response = await open_ai_client.handle_user_message(message)

        if response is not None:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

    async def _get_open_ai_client(self, username: str) -> OpenAiUserClient | None:
        if username not in self._open_ai_clients:
            user_telegram_data = await self._get_user_telegram_data(username)

            self._open_ai_clients[username] = self._open_ai_user_client_builder.build(
                user_id=user_telegram_data.user.id
            )

        return self._open_ai_clients.get(username)

    async def _get_user_telegram_data(self, username: str) -> UserTelegramData | None:
        return await self._user_telegram_integration_repository.get_user_telegram_data_by_username(username)

    async def _get_user_telegram_data_by_user_id(self, user_id: UserId) -> UserTelegramData | None:
        return await self._user_telegram_integration_repository.get_user_telegram_data_by_user_id(user_id)

    async def _update_user_chat_id(self, username: str, chat_id: int) -> None:
        await self._user_telegram_integration_repository.update_user_telegram_chat_id(
            username=username,
            chat_id=chat_id
        )
