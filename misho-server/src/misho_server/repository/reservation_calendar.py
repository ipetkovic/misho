from dataclasses import dataclass
from misho_server.domain.reservation_calendar import CourtReservation, ReservationCalendar
from sqlalchemy import Sequence, delete, select, tuple_
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import selectinload
import misho_server.database.model as dao
from misho_server.domain.reservation_slot import ReservationSlot
from misho_server.repository.time_slot import find_times_slots
from misho_server.repository.time_slot import to_domain as time_slot_to_domain


class ReservationCalendarRepository:
    async def get_calendar(self) -> ReservationCalendar | None:
        raise NotImplementedError()

    async def set_calendar(self, calendar: ReservationCalendar) -> None:
        raise NotImplementedError()


@dataclass
class UpdateCalendar:
    to_insert: dict[ReservationSlot, CourtReservation]
    to_update: dict[ReservationSlot, CourtReservation]
    to_delete: list[ReservationSlot]


class ReservationCalendarRepositorySqlite(ReservationCalendarRepository):
    def __init__(self, engine: AsyncEngine):
        self._engine = engine
        self._sessionmaker = async_sessionmaker(
            bind=engine, expire_on_commit=False)

    async def get_calendar(self) -> ReservationCalendar | None:
        async with self._sessionmaker() as session:
            calendar_dao = await self._load_calendar(session)
            return _to_domain(calendar_dao) if calendar_dao else None

    async def set_calendar(self, calendar: ReservationCalendar) -> None:
        async with self._sessionmaker() as session:

            old_calendar_dao = await self._load_calendar(session)

            print(len(old_calendar_dao))
            old_calendar = _to_domain(
                old_calendar_dao
            ) if old_calendar_dao else None

            update_calendar = self._calculate_diff(
                old_calendar=old_calendar,
                new_calendar=calendar
            )

            times_slots_from_calendars = list(
                calendar.calendar.keys())
            if old_calendar is not None:
                times_slots_from_calendars += list(
                    old_calendar.calendar.keys())

            time_slots = set(
                reservation_slot.time_slot
                for reservation_slot in times_slots_from_calendars)
            time_slot_ids = await find_times_slots(session, time_slots)

            def to_dao_reservation_calendar(
                reservation_slot: ReservationSlot,
                court_reservations: CourtReservation
            ) -> dao.ReservationCalendar:
                return dao.ReservationCalendar(
                    time_slot_id=time_slot_ids[reservation_slot.time_slot],
                    court_id=reservation_slot.court,
                    reserved_by=court_reservations.reserved_by
                )

            to_insert = update_calendar.to_insert
            to_insert.update(update_calendar.to_update)

            # print("to insert: ", to_insert.keys())

            insert = [
                to_dao_reservation_calendar(
                    reservation_slot, court_reservations)
                for reservation_slot, court_reservations in to_insert.items()
            ]

            for obj in insert:
                await session.merge(obj)

            to_delete = [
                (time_slot_ids[reservation_slot.time_slot],
                 reservation_slot.court)
                for reservation_slot in update_calendar.to_delete
            ]

            delete_stmt = delete(dao.ReservationCalendar).where(
                tuple_(
                    dao.ReservationCalendar.time_slot_id,
                    dao.ReservationCalendar.court_id
                ).in_(to_delete)
            )

            await session.execute(delete_stmt)
            await session.commit()

    def _calculate_diff(
        self,
        old_calendar: ReservationCalendar | None,
        new_calendar: ReservationCalendar
    ) -> UpdateCalendar:

        if old_calendar is None:
            old_calendar = ReservationCalendar(calendar={})

        to_insert = {
            reservation_slot: court_reservations
            for reservation_slot, court_reservations in new_calendar.calendar.items()
            if reservation_slot not in old_calendar.calendar
        }

        print("to insert: ", to_insert.keys())

        to_update = {
            reservation_slot: court_reservations
            for reservation_slot, court_reservations in new_calendar.calendar.items()
            if reservation_slot in old_calendar.calendar and
            court_reservations != old_calendar.calendar[reservation_slot]
        }

        print("to update: ", to_update.keys())

        to_delete = [
            reservation_slot
            for reservation_slot in old_calendar.calendar.keys()
            if reservation_slot not in new_calendar.calendar
        ]

        print("to delete: ", to_delete)

        return UpdateCalendar(to_insert=to_insert,
                              to_update=to_update,
                              to_delete=to_delete)

    async def _load_calendar(self, session: AsyncSession) -> Sequence[dao.ReservationCalendar]:
        stmt = select(dao.ReservationCalendar).options(
            selectinload(dao.ReservationCalendar.time_slot)
            .selectinload(dao.TimeSlot.hour_slot)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


def _to_domain(data: Sequence[dao.ReservationCalendar]) -> ReservationCalendar:
    calendar_dict = {}
    for row in data:
        time_slot = row.time_slot
        reservation_slot = ReservationSlot(
            time_slot=time_slot_to_domain(time_slot),
            court=row.court_id
        )

        calendar_dict[reservation_slot] = CourtReservation(
            reserved_by=row.reserved_by)
    return ReservationCalendar(calendar=calendar_dict)
