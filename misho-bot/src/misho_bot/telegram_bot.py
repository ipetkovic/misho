import asyncio
import logging
from misho_bot.open_ai_user_client import OpenAiUserClient
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
_MISHO_SERVER_URL = "http://ec2-52-57-94-53.eu-central-1.compute.amazonaws.com:8000"


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Pozdrav! Ja sam Misho bot, "
        "tu sam da ti pomognem s rezervacijama i obavijestima za teniske terene. "
        "Možeš mi postaviti pitanja ili zatražiti pomoć oko rezervacija. "
        "Kako ti mogu pomoći?"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)


async def handle_message(open_ai_clients: dict[str, OpenAiUserClient], update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    message = update.message.text
    open_ai_client = open_ai_clients.get(update.effective_user.username)

    if not open_ai_client or message is None:
        return None

    print(update.effective_chat.id)

    response = await open_ai_client.handle_user_message(message)

    if response is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def http_server(telegram_application: Application):
    app = web.Application()

    async def handle_notification(request: web.Request) -> web.Response:
        data = await request.json()
        print(f"Received notification: {data}")
        notification = NotificationApi(**data)
        user_info = next(
            filter(lambda user: user.sportbooking_username == notification.username, USERS))

        await telegram_application.bot.send_message(
            chat_id=user_info.chat_id,
            text=notification.message
        )
        return web.Response()

    app.add_routes([web.post(
        '/notifications', handle_notification)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8001)
    await site.start()


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
