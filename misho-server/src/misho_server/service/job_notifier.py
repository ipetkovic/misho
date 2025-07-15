import logging
from misho_server.core.job_notification import JobNotification
from misho_server.core.job_notification.job_notifications_repository import JobNotificationsRepository
from misho_server.service.notification_service import NotificationService


class JobNotifier:
    def __init__(self, job_notifications_repository: JobNotificationsRepository, notification_service: NotificationService):
        self._job_notifications_repository = job_notifications_repository
        self._notification_service = notification_service

    async def handle(self):
        """
        Handle job notifications by fetching available notifications and processing them.
        """
        logging.info("Handling job notifications")
        notifications = await self._job_notifications_repository.get_notifications()
        for notification in notifications:
            await self._process_notification(notification)

    async def _process_notification(self, notification: JobNotification):
        await self._notify(notification)
        await self._job_notifications_repository.update_job_notification_state(
            notification.job_notification_id, trigger_on_available=not notification.is_available())

    async def _notify(self, notification: JobNotification):
        """
        Notify the user about the available reservation slot.
        This method should be implemented to send notifications via email, SMS, etc.
        """

        msg = f"Teren {notification.reservation_slot.court} - {notification.reservation_slot.time_slot} " + (
            "je slobodan za rezervaciju" if notification.is_available()
            else f"rezerviran od strane: {notification.reserved_by}"
        )

        await self._notification_service.send_notification(
            user=notification.job.user, message=msg
        )
