from misho_server.domain.job_notification import JobNotification
from misho_server.repository.job_notifications_repository import JobNotificationsRepository
from misho_server.service import mail_service


class JobNotifier:
    def __init__(self, job_notifications_repository: JobNotificationsRepository, mail_service: mail_service.MailService):
        self._job_notifications_repository = job_notifications_repository
        self._mail_service = mail_service

    async def handle(self):
        """
        Handle job notifications by fetching available notifications and processing them.
        """
        notifications = await self._job_notifications_repository.get_notifications()
        print(f'notifications: {notifications}')
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

        await self._mail_service.send_email(
            to=notification.job.user.email,
            subject="Sportbooking obavijest",
            body=msg
        )
