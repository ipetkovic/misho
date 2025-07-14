import os
from apscheduler.triggers.cron import CronTrigger

from misho_server.config.model import Config, JobCreateConfig, JobExpiredHandlerConfig, JobNotifierConfig, LoggingConfig, MailerConfig, ReservationCalendarSyncConfig, ReservationMonitoringConfig, ReservationNotificationServiceConfig

_MAIL_USERNAME = os.getenv('MISHO_MAIL_USERNAME')
_MAIL_PASSWORD = os.getenv('MISHO_MAIL_PASSWORD')
_TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

print(os.environ.keys())


CONFIG_DEV = Config(
    database_path='db/sportbooking.db',
    dummy_reservation=False,
    update_job_status=True,
    logging=LoggingConfig(
        level='DEBUG'
    ),
    reservation_monitoring=ReservationMonitoringConfig(
        cron=CronTrigger(hour='*', minute='*', second='0,10,20,30,40,50'),
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
        cron=CronTrigger(hour='*', minute='*', second='0')
    ),
    mailer_config=MailerConfig(
        hostname="smtp.gmail.com",
        port=587,
        username=_MAIL_USERNAME,
        password=_MAIL_PASSWORD
    ),
    telegram_bot_token=_TELEGRAM_TOKEN,
    job_create_config=JobCreateConfig(
        default_reserve_job_expire_before_hours=10
    )
)
