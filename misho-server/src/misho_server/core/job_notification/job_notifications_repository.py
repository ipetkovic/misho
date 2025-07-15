from misho_server.core.job_notification import JobNotificationId, JobNotification


class JobNotificationsRepository:
    async def get_notifications(self) -> list[JobNotification]:
        raise NotImplementedError()

    async def update_job_notification_state(
        self,
        job_notification_state_id: JobNotificationId,
        trigger_on_available: bool
    ) -> None:
        raise NotImplementedError()
