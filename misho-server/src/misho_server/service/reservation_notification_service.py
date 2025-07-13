from datetime import datetime, timedelta
from typing import DefaultDict
from misho_server.domain.time_slot import TimeSlot
from misho_server.domain.user import UserId
from misho_server.repository.user import UserRepository
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
        notification_service: NotificationService
    ):
        self._reservation_calendar_service = reservation_calendar_service
        self._user_repository = user_repository
        self._notification_service = notification_service
        self._user_time_slots: DefaultDict[UserTimeSlot, bool] = DefaultDict(
            bool)
        self._notify_before_hours = 10  # hours before the reservation to notify

    async def handle(self):
        users = await self._user_repository.list_users()

        for user in users:
            reservations = await self._reservation_calendar_service.get_calendar(user.id)

            if reservations is not None:
                for reservation_slot in reservations.calendar.keys():
                    user_time_slot = UserTimeSlot(
                        user_id=user.id,
                        time_slot=reservation_slot.time_slot
                    )

                    if self._user_time_slots[user_time_slot] is False and self._should_notify(reservation_slot.time_slot):
                        reservation_cancel_latest_time = reservation_slot.time_slot.start_time() - \
                            timedelta(hours=8)

                        time_delta = reservation_slot.time_slot.start_time() - datetime.now()

                        total_seconds = int(time_delta.total_seconds())
                        hours = round(total_seconds / 3600)

                        message = (
                            'Podsjetnik!\n'
                            f'Imate rezervaciju za {hours} sati.\n'
                            f'Termin je sljedeći: {reservation_slot.time_slot} - teren {reservation_slot.court}.\n'
                            f'Otkazivanje rezervacije je moguće najkasnije do '
                            f'{reservation_cancel_latest_time.strftime('%d.%m.%Y %H:%M')}.'
                        )

                        await self._notification_service.send_notification(user, message)
                        self._user_time_slots[user_time_slot] = True

    def _should_notify(self, time_slot: TimeSlot) -> bool:
        notify_time = time_slot.start_time() - timedelta(
            hours=self._notify_before_hours)

        time_window = timedelta(minutes=5)
        return datetime.now() >= notify_time and datetime.now() < notify_time + time_window
