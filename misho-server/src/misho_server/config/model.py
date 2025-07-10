from dataclasses import dataclass
from apscheduler.triggers.cron import CronTrigger


@dataclass
class ReservationMonitoringConfig:
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
class JobCreateConfig:
    default_reserve_job_expire_before_hours: int


@dataclass
class Config:
    database_path: str
    dummy_reservation: bool
    update_job_status: bool
    logging: LoggingConfig
    reservation_monitoring: ReservationMonitoringConfig
    mailer_config: MailerConfig
    telegram_bot_token: str
