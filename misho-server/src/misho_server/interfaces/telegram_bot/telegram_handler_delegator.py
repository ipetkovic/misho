from enum import Enum
from misho_server.core.user import User
from misho_server.core.user_telegram import UserTelegramData
from misho_server.core.user_telegram.user_telegram_integration_repository import UserTelegramIntegrationRepository
from misho_server.interfaces.telegram_bot.blacklisted_handler import TelegramBlacklistedUserHandler
from misho_server.interfaces.telegram_bot.common import get_username
from misho_server.interfaces.telegram_bot.onboarding_handler import TelegramOnboardingHandler
from misho_server.interfaces.telegram_bot.standard_handler import TelegramStandardHandler
from misho_server.interfaces.telegram_bot.telegram_handler import ChatId, TelegramHandler
from telegram import Update
from telegram.ext import ContextTypes


class TelegramUserState(Enum):
    BLACKLISTED = "BLACKLISTED"
    ONBOARDING = "ONBOARDING"
    ONBOARDED = "ONBOARDED"


class TelegramHandlerDelegator(TelegramHandler):
    def __init__(
        self,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
        blacklisted_handler: TelegramBlacklistedUserHandler,
        onboarding_handler: TelegramOnboardingHandler,
        standard_handler: TelegramStandardHandler,
    ):
        self._user_telegram_integration_repository = user_telegram_integration_repository
        self._handlers: dict[TelegramUserState, TelegramHandler] = {
            TelegramUserState.BLACKLISTED: blacklisted_handler,
            TelegramUserState.ONBOARDING: onboarding_handler,
            TelegramUserState.ONBOARDED: standard_handler,
        }

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = get_username(update)
        if username is None:
            return

        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.start_handler(update, context)

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = get_username(update)
        if username is None:
            return

        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.signup_handler(update, context)

    async def handle_message_notification(self, user: User, message: str) -> ChatId | None:
        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_user_id(
            user.id)
        handler = self._get_handler(user_telegram_data)
        return await handler.handle_message_notification(user, message)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = get_username(update)
        if username is None:
            return

        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.message_handler(update, context)

    def _get_handler(self, user_telegram_data: UserTelegramData | None) -> TelegramHandler:
        state = self._get_state(user_telegram_data)
        handler = self._handlers[state]
        return handler

    def _get_state(self, user_telegram_data: UserTelegramData | None) -> TelegramUserState:
        if user_telegram_data is None:
            return TelegramUserState.BLACKLISTED
        if user_telegram_data.user is None:
            return TelegramUserState.ONBOARDING
        return TelegramUserState.ONBOARDED
