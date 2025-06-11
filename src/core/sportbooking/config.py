from dataclasses import dataclass
from apscheduler.triggers.cron import CronTrigger


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
