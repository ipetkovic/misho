from dataclasses import dataclass
from apscheduler.triggers.cron import CronTrigger


@dataclass
class ReservationMonitoringConfig:
    cron: CronTrigger


@dataclass
class ReservationCalendarSyncConfig:
    cron: CronTrigger


@dataclass
class JobExpiredHandlerConfig:
    cron: CronTrigger


@dataclass
class JobNotifierConfig:
    cron: CronTrigger


@dataclass
class ReservationNotificationServiceConfig:
    cron: CronTrigger
    notify_before_minutes: tuple[int, ...]  # in minutes


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
    job_create_config: JobCreateConfig
    reservation_monitoring: ReservationMonitoringConfig
    reservation_calendar_sync: ReservationCalendarSyncConfig
    job_expired_handler: JobExpiredHandlerConfig
    job_notifier: JobNotifierConfig
    reservation_notification_service: ReservationNotificationServiceConfig
    mailer_config: MailerConfig
    telegram_bot_token: str
