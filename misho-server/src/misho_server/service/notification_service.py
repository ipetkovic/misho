

import logging
from httpx import AsyncClient, Request
from misho_server.database.model import User
from misho_server.service.mail_service import MailService

from misho_api.notification import NotificationApi


class NotificationService:
    def __init__(self, http_client: AsyncClient, mail_service: MailService, notification_webhook_url: str | None):
        self._mail_service = mail_service
        self._http_client = http_client
        self._webhook_url = notification_webhook_url

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

        if self._webhook_url is not None:
            data = NotificationApi(
                username=user.username,
                message=message
            )

            try:
                request = Request(
                    method="POST",
                    url=self._webhook_url,
                    data=data.model_dump_json()
                )
                await self._http_client.send(request)
            except Exception as e:
                logging.error(
                    f"Failed to send notification to webhook {self._webhook_url}: {e}")
