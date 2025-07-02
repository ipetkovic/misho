from enum import Enum
from misho_server.domain.user import User
from misho_server.domain.user_telegram_data import UserTelegramData
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepository
from misho_server.service.telegram_bot.blacklisted_handler import TelegramBlacklistedUserHandler
from misho_server.service.telegram_bot.onboarding_handler import TelegramOnboardingHandler
from misho_server.service.telegram_bot.standard_handler import TelegramStandardHandler
from misho_server.service.telegram_bot.telegram_handler import ChatId, TelegramHandler
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
        self._handlers = {
            TelegramUserState.BLACKLISTED: blacklisted_handler,
            TelegramUserState.ONBOARDING: onboarding_handler,
            TelegramUserState.ONBOARDED: standard_handler,
        }

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=update.effective_user.username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.start_handler(update, context)

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=update.effective_user.username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.signup_handler(update, context)

    async def get_chat_id_for_notifications(self, user: User) -> ChatId | None:
        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_user_id(
            user.id)
        handler = self._get_handler(user_telegram_data)
        return await handler.get_chat_id_for_notifications(user)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_telegram_data = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username=update.effective_user.username
        )
        handler = self._get_handler(user_telegram_data)
        await handler.message_handler(update, context)

    def _get_handler(self, user_telegram_data: UserTelegramData | None) -> TelegramHandler:
        state = self._get_state(user_telegram_data)
        return self._handlers.get(state)

    def _get_state(self, user_telegram_data: UserTelegramData | None) -> TelegramUserState:
        if user_telegram_data is None:
            return TelegramUserState.BLACKLISTED
        if user_telegram_data.user is None:
            return TelegramUserState.ONBOARDING
        return TelegramUserState.ONBOARDED
