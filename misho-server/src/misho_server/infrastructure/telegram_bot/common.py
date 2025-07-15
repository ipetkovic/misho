from misho_server.infrastructure.telegram_bot.telegram_handler import ChatId
from telegram import Update


def get_username(update: Update) -> str | None:
    if update.effective_user is None or update.effective_user.username is None:
        return None
    return update.effective_user.username


def get_chat_id(update: Update) -> ChatId | None:
    if update.effective_chat is None:
        return None
    return update.effective_chat.id


def get_message_text(update: Update) -> str | None:
    if update.message is None or update.message.text is None:
        return None
    return update.message.text
