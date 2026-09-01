import os
from apscheduler.triggers.cron import CronTrigger

from misho_server.config.model import Config, JobCreateConfig, JobExpiredHandlerConfig, JobNotifierConfig, LoggingConfig, ReservationCalendarSyncConfig, ReservationMonitoringConfig, ReservationNotificationServiceConfig

_TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
_ADMIN_TELEGRAM_USERNAME = os.getenv('MISHO_ADMIN_TELEGRAM_USERNAME', '')


CONFIG_PROD = Config(
    database_path='db/sportbooking.db',
    dummy_reservation=False,
    update_job_status=True,
    logging=LoggingConfig(
        level='INFO'
    ),
    reservation_monitoring=ReservationMonitoringConfig(
        cron=CronTrigger(hour='*', minute='*', second='0, 30')
    ),
    reservation_calendar_sync=ReservationCalendarSyncConfig(
        cron=CronTrigger(hour='*', minute='*', second='25,55'),
    ),
    job_expired_handler=JobExpiredHandlerConfig(
        cron=CronTrigger(hour='*', minute='*', second='0')
    ),
    job_notifier=JobNotifierConfig(
        cron=CronTrigger(hour='*', minute='*', second='0,30')
    ),
    reservation_notification_service=ReservationNotificationServiceConfig(
        cron=CronTrigger(hour='*', minute='*', second='0'),
        notify_before_minutes=(10 * 60, 8 * 60 + 30)
    ),
    telegram_bot_token=_TELEGRAM_TOKEN,
    admin_telegram_username=_ADMIN_TELEGRAM_USERNAME,
    job_create_config=JobCreateConfig(
        default_reserve_job_expire_before_hours=10
    )
)
