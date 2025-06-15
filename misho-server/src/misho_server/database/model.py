from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Enum, ForeignKey, Date, String, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.associationproxy import association_proxy
import datetime

from misho_server.domain.job import Status
from misho_server.domain.monitoring_job import MonitoringAction


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    name: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=True)
    app_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=True)


class UserToken(Base):
    __tablename__ = 'user_tokens'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True)
    token: Mapped[str]
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now, onupdate=datetime.datetime.now)

    user: Mapped[User] = relationship(User)


class TimeSlot(Base):
    __tablename__ = 'time_slots'
    __table_args__ = (
        UniqueConstraint('date', 'hour_slot_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date)
    hour_slot_id: Mapped[int] = mapped_column(
        ForeignKey("hour_slots.id"))
    hour_slot: Mapped["HourSlot"] = relationship(
        'HourSlot',
        back_populates="time_slots"
    )


class HourSlot(Base):
    __tablename__ = 'hour_slots'
    __table_args__ = (
        UniqueConstraint('from_hour', 'to_hour'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_hour: Mapped[int]
    to_hour: Mapped[int]
    time_slots: Mapped[List[TimeSlot]] = relationship(
        'TimeSlot', back_populates="hour_slot"
    )


class Court(Base):
    __tablename__ = 'courts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str]


class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = (
        UniqueConstraint('user_id', 'time_slot_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    time_slot_id: Mapped[int] = mapped_column(ForeignKey("time_slots.id"))
    status: Mapped[Status] = mapped_column(
        Enum(Status), default=Status.PENDING)
    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now)

    user: Mapped[User] = relationship(User)
    time_slot: Mapped[TimeSlot] = relationship(TimeSlot)
    job_courts: Mapped[List['JobCourt']] = relationship(
        'JobCourt',
        back_populates="job",
        cascade="all, delete-orphan"
    )
    monitoring_job: Mapped[Optional['MonitoringJob']] = relationship(
        'MonitoringJob',
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan"
    )


class JobCourt(Base):
    __tablename__ = 'job_courts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"))
    court_id: Mapped[int] = mapped_column(
        ForeignKey("courts.id"))
    priority: Mapped[int]

    job: Mapped[Job] = relationship(Job, back_populates="job_courts")
    court: Mapped[Court] = relationship(Court)
    notification_state: Mapped['JobNotificationState'] = relationship(
        'JobNotificationState',
        back_populates="job_court",
        uselist=False,
        cascade="all, delete-orphan"
    )


class MonitoringJob(Base):
    __tablename__ = 'monitoring_jobs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    action: Mapped[MonitoringAction] = mapped_column(Enum(MonitoringAction))

    job: Mapped[Job] = relationship(
        Job, back_populates="monitoring_job")


class ReservationCalendar(Base):
    __tablename__ = 'reservation_calendar'

    time_slot_id: Mapped[int] = mapped_column(
        ForeignKey("time_slots.id"), primary_key=True)
    court_id: Mapped[int] = mapped_column(
        ForeignKey("courts.id"), primary_key=True)
    reserved_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now, onupdate=datetime.datetime.now)

    time_slot = relationship(TimeSlot)


class JobNotificationState(Base):
    __tablename__ = 'job_notification_states'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_court_id: Mapped[int] = mapped_column(ForeignKey("job_courts.id"))
    trigger_on_available: Mapped[bool] = mapped_column()
    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now, onupdate=datetime.datetime.now)

    job_court: Mapped['JobCourt'] = relationship(
        "JobCourt", back_populates="notification_state"
    )
    job: Mapped[Job] = association_proxy("job_court", "job")
