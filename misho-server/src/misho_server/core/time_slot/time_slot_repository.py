from datetime import date

type TimeSlotId = int


class TimeSlotRepository:
    async def insert_time_slots(self, start_date: date, number_of_days: int) -> None:
        raise NotImplementedError()
