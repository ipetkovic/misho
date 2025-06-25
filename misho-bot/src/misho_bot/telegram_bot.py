import logging
from misho_bot.open_ai_user_client import OpenAiUserClient
from misho_client import Authorization
from misho_client.job_client import JobClient
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes

import os
from openai import OpenAI


_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
_MISHO_SERVER_URL = "http://ec2-52-57-94-53.eu-central-1.compute.amazonaws.com:8000"

USERS = {
    'Mojo28': Authorization(token=os.environ.get("MISHO_ACCESS_KEY", None))
}

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

    response = open_ai_client.handle_user_message(message)

    if response is not None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


def main():
    open_ai_client = OpenAI()
    job_client = JobClient(_MISHO_SERVER_URL)

    open_ai_clients = {
        user: OpenAiUserClient(
            open_ai_client=open_ai_client,
            job_client=job_client,
            authorization=authorization
        ) for user, authorization in USERS.items()
    }

    application = ApplicationBuilder().token(_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await handle_message(open_ai_clients, update, context)
        return result

    message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(message_handler)

    application.run_polling()
