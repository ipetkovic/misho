

import logging
from misho_server.database.model import User
from misho_server.service.mail_service import MailService

from misho_api.notification import NotificationApi


class NotificationService:
    def __init__(self, mail_service: MailService):
        self._mail_service = mail_service

    async def send_notification(self, user: User, message: str) -> None:
        if user.email is not None:
            try:
                await self._mail_service.send_email(
                    to=user.email,
                    subject="Sportbooking obavijest",
                    body=message
                )

            except Exception as e:
                logging.error(f"Failed to send email to {user.email}: {e}")
