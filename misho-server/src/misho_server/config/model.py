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
class HealthConfig:
    # Port for the /healthz endpoint. Only ever reached from inside the
    # container -- the Docker HEALTHCHECK and the deploy rollout poll it -- so
    # it is deliberately not exposed through the GCP firewall.
    port: int


@dataclass
class JobCreateConfig:
    default_reserve_job_expire_before_hours: int


@dataclass
class Config:
    database_path: str
    dummy_reservation: bool
    update_job_status: bool
    logging: LoggingConfig
    health: HealthConfig
    job_create_config: JobCreateConfig
    reservation_monitoring: ReservationMonitoringConfig
    reservation_calendar_sync: ReservationCalendarSyncConfig
    job_expired_handler: JobExpiredHandlerConfig
    job_notifier: JobNotifierConfig
    reservation_notification_service: ReservationNotificationServiceConfig
    telegram_bot_token: str
    # Telegram username (no leading @) that is allow-listed on startup and may
    # run /invite. Empty disables both -- the allow-list then has to be seeded
    # by hand.
    admin_telegram_username: str
