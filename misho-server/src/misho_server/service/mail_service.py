from asyncio.log import logger
from email.message import EmailMessage
import aiosmtplib

from misho_server.config.model import MailerConfig


class MailService:
    def __init__(self, mail_config: MailerConfig):
        self._mailer_config = mail_config

    async def send_email(self, to: str, subject: str, body: str):
        msg = EmailMessage()
        msg["From"] = self._mailer_config.username
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=self._mailer_config.hostname,
            port=self._mailer_config.port,
            start_tls=True,
            username=self._mailer_config.username,
            password=self._mailer_config.password,
        )

        logger.info("Email sent successfully")
