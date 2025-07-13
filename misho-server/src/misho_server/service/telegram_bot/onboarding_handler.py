import logging
import shlex
from misho_server.domain.user import User
from misho_server.repository.user_telegram_integration import UserTelegramIntegrationRepository
from misho_server.service.signup_service import SignUpService
from misho_server.service.telegram_bot.common import get_chat_id, get_message_text, get_username
from misho_server.service.telegram_bot.telegram_handler import ChatId, TelegramHandler
from telegram import Update
from telegram.ext import ContextTypes


class TelegramOnboardingHandler(TelegramHandler):
    def __init__(
        self,
        signup_service: SignUpService,
        user_telegram_integration_repository: UserTelegramIntegrationRepository,
    ):
        self._signup_service = signup_service
        self._user_telegram_integration_repository = user_telegram_integration_repository

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = get_chat_id(update)
        if not chat_id:
            return

        message = (
            "Pozdrav! Ja sam Misho bot, "
            "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene.\n"
            "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija.\n"

            "Prije nego što počnemo, moraš se registrirati sa Sportbooking korisničkim imenom i lozinkom.\n\n"
            "To možeš učiniti tako da pošalješ poruku u formatu:\n"
            "/signup <korisničko_ime> <lozinka>\n\n"
            "Ukoliko korisničko ime i/ili lozinka sadrže razmake, koristi navodnike. Primjer:\n"
            "/signup \"korisničko ime\" \"lozinka\""
        )
        await context.bot.send_message(chat_id=chat_id, text=message)

    async def handle_message_notification(self, user: User) -> ChatId | None:
        return None

    async def signup_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        username = get_username(update)
        message = get_message_text(update)
        chat_id = get_chat_id(update)

        logging.info(
            f"Signup handler called for user {username}")

        if not username or not message or not chat_id:
            return

        text = message.partition(' ')[2]
        text = text.replace('“', '"')
        text = text.replace('”', '"')
        text = text.replace("‘", "'")
        text = text.replace("’", "'")

        try:
            args = shlex.split(text)
            username, password = args
            user = await self._signup_service.sign_up(username=username, password=password)
            await self._user_telegram_integration_repository.update_user_telegram_user_id(
                username,
                user.id
            )
            logging.info(f"Sign-up successful for user {user}")
            message = 'Registracija uspješna! Kako ti mogu pomoći?'
        except Exception as e:
            logging.error(f"Error during signup: {e}")
            message = 'Došlo je do greške prilikom registracije. Provjeri korisničko ime i lozinku i pokušaj ponovno.'

        await context.bot.send_message(chat_id=chat_id, text=message)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = get_chat_id(update)
        if not chat_id:
            return

        message = "Prije nego počnemo, moraš se registrirati sa /start komandom."
        await context.bot.send_message(chat_id=chat_id, text=message)
