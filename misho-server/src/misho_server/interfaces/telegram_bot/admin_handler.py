import logging

from misho_server.interfaces.telegram_bot.common import get_chat_id, get_message_text, get_username
from misho_server.service.telegram_invite_service import TelegramInviteService, normalize_telegram_username
from telegram import Update
from telegram.ext import ContextTypes


class TelegramAdminHandler:
    """/invite -- the one command gated on *who* is asking rather than on the
    sender's onboarding state, so it deliberately sits outside
    `TelegramHandlerDelegator`'s state machine.
    """

    def __init__(
        self,
        admin_username: str,
        telegram_invite_service: TelegramInviteService,
    ):
        self._admin_username = admin_username
        self._telegram_invite_service = telegram_invite_service

    async def invite_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        chat_id = get_chat_id(update)
        message = get_message_text(update)

        if username is None or chat_id is None or message is None:
            return

        if not self._is_admin(username):
            # The same silence the blacklist handler gives -- no reason to tell
            # a stranger that the command exists.
            logging.info("Ignoring /invite from non-admin user: %s", username)
            return

        args = message.partition(' ')[2].split()
        if len(args) != 1:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Koristi: /invite <telegram_korisničko_ime>"
            )
            return

        invitee = normalize_telegram_username(args[0])
        created = await self._telegram_invite_service.invite(invitee)

        if created:
            text = (
                f"@{invitee} sada ima pristup. Neka pošalje /start botu.\n\n"
                "Ako se ništa ne dogodi, provjeri velika i mala slova — "
                "korisničko ime mora biti točno onakvo kakvo je na Telegramu."
            )
        else:
            text = f"@{invitee} već ima pristup."

        await context.bot.send_message(chat_id=chat_id, text=text)

    def _is_admin(self, username: str) -> bool:
        if not self._admin_username:
            return False
        return username.casefold() == self._admin_username.casefold()
