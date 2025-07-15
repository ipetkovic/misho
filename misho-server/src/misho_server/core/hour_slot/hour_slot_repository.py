from misho_server.core.hour_slot import HourSlot


class HourSlotRepository:
    async def list_hour_slots(self) -> list[HourSlot]:
        raise NotImplementedError()
