import logging
from typing import Awaitable, Callable
from misho_server.database.model import User


type NotificationServiceSubscriber = Callable[[User, str], Awaitable[None]]


class NotificationService:
    def __init__(self):
        self._subscribers: list[NotificationServiceSubscriber] = []

    def subscribe(self, subscriber: NotificationServiceSubscriber) -> None:
        self._subscribers.append(subscriber)

    async def send_notification(self, user: User, message: str) -> None:
        for subscriber in self._subscribers:
            try:
                await subscriber(user, message)
            except Exception as e:
                logging.error(
                    f"Error sending notification to {user.email}: {e}")
