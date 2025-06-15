import os
from apscheduler.triggers.cron import CronTrigger

from misho_server.config.model import Config, LoggingConfig, MailerConfig, ReservationMonitoringConfig

_MAIL_USERNAME = os.getenv('MISHO_MAIL_USERNAME')
_MAIL_PASSWORD = os.getenv('MISHO_MAIL_PASSWORD')

print(os.environ.keys())


CONFIG_DEV = Config(
    database_path='db/sportbooking.db',
    dummy_reservation=False,
    update_job_status=True,
    logging=LoggingConfig(
        level='DEBUG'
    ),
    reservation_monitoring=ReservationMonitoringConfig(
        username="Ivo Petkovic",
        cron=CronTrigger(hour='3', minute='*', second='0, 10, 20, 30, 40, 50')
    ),
    mailer_config=MailerConfig(
        hostname="smtp.gmail.com",
        port=587,
        username=_MAIL_USERNAME,
        password=_MAIL_PASSWORD
    )

)
