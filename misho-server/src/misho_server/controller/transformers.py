

from misho_server.domain.hour_slot import HourSlot
from misho_server.domain.time_slot import TimeSlot
from misho_api.hour_slot import HourSlotApi
from misho_api.time_slot import TimeSlotApi


def hour_slot_to_api(hour_slot: HourSlot) -> HourSlotApi:
    return HourSlotApi(
        from_hour=hour_slot.from_hour,
        to_hour=hour_slot.to_hour
    )


def hour_slot_from_api(hour_slot_api: HourSlotApi) -> HourSlot:
    return HourSlot(
        from_hour=hour_slot_api.from_hour,
        to_hour=hour_slot_api.to_hour
    )


def time_slot_to_api(time_slot: TimeSlot) -> TimeSlotApi:
    return TimeSlotApi(
        date=time_slot.date,
        hour_slot=hour_slot_to_api(time_slot.hour_slot)
    )


def time_slot_from_api(time_slot_api: TimeSlotApi) -> TimeSlot:
    return TimeSlot(
        date=time_slot_api.date,
        hour_slot=hour_slot_from_api(time_slot_api.hour_slot)
    )
