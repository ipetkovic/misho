from dataclasses import dataclass
import os
from apscheduler.triggers.cron import CronTrigger

_MAIL_USERNAME = os.getenv('MISHO_MAIL_USERNAME')
_MAIL_PASSWORD = os.getenv('MISHO_MAIL_PASSWORD')


@dataclass
class ReservationMonitoringConfig:
    username: str
    cron: CronTrigger


@dataclass
class LoggingConfig:
    level: str


@dataclass
class MailerConfig:
    hostname: str
    port: int
    username: str
    password: str


@dataclass
class Config:
    database_path: str
    dummy_reservation: bool
    update_job_status: bool
    logging: LoggingConfig
    reservation_monitoring: ReservationMonitoringConfig
    mailer_config: MailerConfig


CONFIG = Config(
    database_path='sportbooking.db',
    dummy_reservation=True,
    update_job_status=True,
    logging=LoggingConfig(
        level='DEBUG'
    ),
    reservation_monitoring=ReservationMonitoringConfig(
        username="Ivo Petkovic",
        cron=CronTrigger(hour='*', minute='*', second='0, 10, 20, 30, 40, 50')
    ),
    mailer_config=MailerConfig(
        hostname="smtp.gmail.com",
        port=587,
        username=_MAIL_USERNAME
        password=_MAIL_PASSWORD
    )

)
