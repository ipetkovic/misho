import os
from apscheduler.triggers.cron import CronTrigger

from misho_server.config.model import Config, LoggingConfig, MailerConfig, ReservationMonitoringConfig

_MAIL_USERNAME = os.getenv('MISHO_MAIL_USERNAME')
_MAIL_PASSWORD = os.getenv('MISHO_MAIL_PASSWORD')


CONFIG_PROD = Config(
    database_path='db/sportbooking.db',
    dummy_reservation=False,
    update_job_status=True,
    logging=LoggingConfig(
        level='INFO'
    ),
    reservation_monitoring=ReservationMonitoringConfig(
        username="Ivo Petkovic",
        cron=CronTrigger(hour='*', minute='*', second='0')
    ),
    mailer_config=MailerConfig(
        hostname="smtp.gmail.com",
        port=587,
        username=_MAIL_USERNAME,
        password=_MAIL_PASSWORD
    )

)
