from datetime import datetime, timedelta
import logging
from typing import DefaultDict
from misho_server.core.time_slot import TimeSlot
from misho_server.core.user import UserId
from misho_server.core.user.user_repository import UserRepository
from misho_server.service.notification_service import NotificationService
from misho_server.service.reservation_calendar import ReservationCalendarService
import pydantic


class UserTimeSlot(pydantic.BaseModel):
    user_id: UserId
    time_slot: TimeSlot

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class ReservationNotificationService:
    def __init__(
        self,
        reservation_calendar_service: ReservationCalendarService,
        user_repository: UserRepository,
        notification_service: NotificationService,
        notify_before_minutes: tuple[int, ...]
    ):
        self._reservation_calendar_service = reservation_calendar_service
        self._user_repository = user_repository
        self._notification_service = notification_service
        self._user_time_slots: DefaultDict[tuple[UserTimeSlot, int], bool] = DefaultDict(
            bool)
        # minutes before the reservation to notify
        self._notify_before_minutes = notify_before_minutes

    async def handle(self):
        logging.info("Handling reservation notifications")
        users = await self._user_repository.list_users()

        for user in users:
            reservations = await self._reservation_calendar_service.get_calendar(user.id)

            if reservations is not None:
                for reservation_slot in reservations.calendar.keys():
                    user_time_slot = UserTimeSlot(
                        user_id=user.id,
                        time_slot=reservation_slot.time_slot
                    )

                    for idx, notify_before in enumerate(self._notify_before_minutes):

                        if self._user_time_slots[(user_time_slot, idx)] is False and self._should_notify(reservation_slot.time_slot, notify_before):
                            reservation_cancel_latest_time = reservation_slot.time_slot.start_time() - \
                                timedelta(hours=8)

                            message = (
                                'Podsjetnik na termin!\n'
                                f'Termin: {reservation_slot.time_slot} - teren {reservation_slot.court}.\n'
                                f'Otkazivanje rezervacije je moguće najkasnije do '
                                f'{reservation_cancel_latest_time.strftime('%d.%m.%Y %H:%M')}.'
                            )

                            await self._notification_service.send_notification(user, message)
                            self._user_time_slots[(user_time_slot, idx)] = True

    def _should_notify(self, time_slot: TimeSlot, notify_before_minutes: int) -> bool:
        notify_time = time_slot.start_time() - timedelta(
            minutes=notify_before_minutes)

        time_window = timedelta(minutes=5)
        return datetime.now() >= notify_time and datetime.now() < notify_time + time_window
