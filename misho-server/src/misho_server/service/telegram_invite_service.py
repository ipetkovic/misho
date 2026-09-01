import logging

from misho_server.core.user_telegram.user_telegram_integration_repository import UserTelegramIntegrationRepository


def normalize_telegram_username(username: str) -> str:
    """Strip the decoration people type around a handle.

    Casing is left alone on purpose: the stored username is matched against
    `update.effective_user.username` verbatim, and Telegram reports whatever
    casing the account was created with.
    """
    return username.strip().lstrip('@')


class TelegramInviteService:
    """Grants a Telegram account access to the bot.

    A row in `user_telegram_notifications` *is* the allow-list --
    `TelegramHandlerDelegator` treats a missing row as blacklisted and drops
    every update from it. So an invite is just that row: the invitee links
    their own sportbooking account afterwards with /signup.
    """

    def __init__(
        self,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
    ):
        self._user_telegram_integration_repository = user_telegram_integration_repository

    async def invite(self, username: str) -> bool:
        """Allow-list `username`.

        Returns True if this created the row, False if it was already there --
        which keeps it safe to call on every startup for the admin.
        """
        username = normalize_telegram_username(username)
        if not username:
            raise ValueError("Telegram username must not be empty.")

        existing = await self._user_telegram_integration_repository.get_user_telegram_data_by_username(
            username
        )
        if existing is not None:
            return False

        await self._user_telegram_integration_repository.create_user_telegram_data(username)
        logging.info("Invited Telegram user: %s", username)
        return True
