import asyncio
import logging
from misho_server.service.open_ai.user_client import OpenAiUserClient
from misho_client import Authorization
from misho_client.job_client import JobClient
from aiohttp import web
import pydantic
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, Application

import os
from openai import OpenAI

from misho_api.notification import NotificationApi


_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
_MISHO_SERVER_URL = "http://localhost:8000"


class UserInfo(pydantic.BaseModel):
    sportbooking_username: str
    telegram_username: str
    app_token: Authorization
    chat_id: int


USERS = [
    UserInfo(
        sportbooking_username='Ivo Petkovic',
        telegram_username='Mojo28',
        app_token=Authorization(
            token=os.environ.get("MISHO_ACCESS_KEY", None)),
        chat_id=314635423
    )
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class TelegramBotApplication:
    def __init__(self, telegram_token: str):
        self._telegram_token = telegram_token
        self._open_ai_clients: dict[str, OpenAiUserClient] = {}
        application = ApplicationBuilder().token(telegram_token).build()

        start_handler = CommandHandler('start', self.start)
        application.add_handler(start_handler)

        message_handler = MessageHandler(
            filters.TEXT & (~filters.COMMAND), self.handle_message)
        application.add_handler(message_handler)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = (
            "Pozdrav! Ja sam Misho bot, "
            "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene. "
            "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija. "
            "Kako ti mogu pomoći?"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
        message = update.message.text
        open_ai_client = open_ai_clients.get(update.effective_user.username)

        if not open_ai_client or message is None:
            return None

        print(update.effective_chat.id)

        response = await open_ai_client.handle_user_message(message)

        if response is not None:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

    def get_open_ai_client(self, username: str) -> OpenAiUserClient:
        if username not in self._open_ai_clients:
            sel.f._open_ai_clients[username] = OpenAiUserClient(
                open_ai_client=OpenAI(),
                job_client=JobClient(_MISHO_SERVER_URL),
                # Assuming all users share the same token
                authorization=USERS[0].app_token
            )

        return self._open_ai_clients[username]


async def run():
    open_ai_client = OpenAI()
    job_client = JobClient(_MISHO_SERVER_URL)

    open_ai_clients = {
        user.telegram_username: OpenAiUserClient(
            open_ai_client=open_ai_client,
            job_client=job_client,
            authorization=user.app_token
        ) for user in USERS
    }

    application = ApplicationBuilder().token(_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    async def message_handler_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await handle_message(open_ai_clients, update, context)
        return result

    message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), message_handler_callback)
    application.add_handler(message_handler)

    async with application:
        await application.start()
        await http_server(application)
        await application.updater.start_polling()
        await asyncio.Event().wait()
        await application.stop()


def main():
    asyncio.run(run())
