from misho_server.core.user import User, UserId
from misho_server.core.user_telegram import UserTelegramData
from misho_server.core.user_telegram.user_telegram_integration_repository import UserTelegramIntegrationRepository
from misho_server.infrastructure.open_ai.tool_handler import OpenAiToolHandler
from misho_server.infrastructure.open_ai.user_client import OpenAiUserClient
from misho_server.infrastructure.telegram_bot.common import get_chat_id, get_message_text, get_username
from misho_server.infrastructure.telegram_bot.telegram_handler import ChatId, TelegramHandler
from openai import OpenAI
from telegram import Update
from telegram.ext import ContextTypes


class OpenAiUserClientBuilder:
    def __init__(
        self,
        open_ai_client: OpenAI,
        open_ai_tool_handler: OpenAiToolHandler,
    ):
        self._open_ai_client = open_ai_client
        self._tool_handler = open_ai_tool_handler

    def build(self, user_id: UserId) -> OpenAiUserClient:
        return OpenAiUserClient(
            open_ai_client=self._open_ai_client,
            tool_handler=self._tool_handler,
            user_id=user_id
        )


class TelegramStandardHandler(TelegramHandler):
    def __init__(
        self,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
        open_ai_user_client_builder: OpenAiUserClientBuilder,
    ):
        self._open_ai_user_client_builder = open_ai_user_client_builder
        self._open_ai_clients: dict[str, OpenAiUserClient] = {}
        self._user_telegram_integration_repository = user_telegram_integration_repository

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        chat_id = get_chat_id(update)

        if username is None or chat_id is None:
            return

        message = (
            "Pozdrav! Ja sam Misho bot, "
            "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene.\n"
            "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija.\n"
        )

        await self._update_user_chat_id(
            username=username,
            chat_id=chat_id
        )
        await context.bot.send_message(chat_id=chat_id, text=message)

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        return None

    async def handle_message_notification(self, user: User, message: str) -> ChatId | None:
        user_telegram_data = await self._get_user_telegram_data_by_user_id(user.id)
        open_ai_client = await self._get_open_ai_client(user.username)
        if open_ai_client is not None:
            open_ai_client.add_system_message_to_context(message)

        return user_telegram_data.chat_id if user_telegram_data else None

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        chat_id = get_chat_id(update)
        message = get_message_text(update)

        if username is None or chat_id is None or message is None:
            return

        open_ai_client = await self._get_open_ai_client(username)
        if open_ai_client is None:
            raise ValueError(f"OpenAI client not found for user: {username}")

        response = await open_ai_client.handle_user_message(message)

        if response is not None:
            await context.bot.send_message(chat_id=chat_id, text=response)

    async def _get_open_ai_client(self, username: str) -> OpenAiUserClient | None:
        if username not in self._open_ai_clients:
            user_telegram_data = await self._get_user_telegram_data(username)

            if user_telegram_data is None or user_telegram_data.user is None:
                return None

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
