from bs4 import BeautifulSoup, Tag
import datetime
from sportbooking.reservation_calendar import CourtId, HourSlot, ReservationSlot, TimeSlot


type Name = str
type NamesCalendar = dict[ReservationSlot, Name]
type NamePerCourt = dict[CourtId, Name]


class NamesParser:
    def __init__(self, soup: BeautifulSoup):
        self._soup = soup

    def parse(self) -> NamesCalendar:
        heads = self._soup.find_all("thead", class_="poimenimavrijemfont")
        tables: list[Tag] = [head.parent for head in heads]  # type: ignore

        def extract_table_date(table: Tag):
            main_div = table.parent.parent  # type: ignore
            assert isinstance(main_div, Tag), "Expected a Tag for table"
            title_div = main_div.find("div")
            assert isinstance(title_div, Tag), "Expected a Tag for title_div"
            day = title_div.text.strip()
            return day.split(',')[1].strip()

        dates = [datetime.datetime.strptime(extract_table_date(table), "%d.%m.%Y").date()
                 for table in tables]

        courts = self._get_courts(tables[0])

        calendar: dict[ReservationSlot, Name] = {}
        for date, table in zip(dates, tables):
            day_calendar = self._parse_day_calendar(date, table, courts)
            calendar.update(day_calendar)

        return calendar

    def _parse_day_calendar(self, date: datetime.date, table: Tag, courts: list[int]) -> dict[ReservationSlot, Name]:
        rows = table.find_all("tbody")
        day_calendar: dict[ReservationSlot, Name] = {}
        for row in rows:
            assert isinstance(row, Tag), "Expected a Tag for tbody"
            tr = row.find('tr')
            assert isinstance(tr, Tag), "Expected a Tag for tr"
            hour_slot, row_names = self._parse_hour_slot(tr, courts)

            for court, name in row_names.items():
                slot = ReservationSlot(
                    time_slot=TimeSlot(
                        date=date,
                        hour_slot=hour_slot,
                    ),
                    court=court
                )
                day_calendar[slot] = name

        return day_calendar

    def _parse_hour_slot(self, row: Tag, court_nums: list[int]) -> tuple[HourSlot, NamePerCourt]:
        columns = row.find_all("td")

        time = _parse_time(columns[0].text.strip())

        names: NamePerCourt = {}
        for court_num, slot in zip(court_nums, columns[1:]):
            assert isinstance(slot, Tag), "Expected a Tag for slot"
            div = slot.find('div')
            if div is not None:
                names[court_num] = div.text.strip()

        return (time, names)

    def _get_courts(self, table: Tag) -> list[int]:
        ths: list[Tag] = table.find("thead").find_all(  # type: ignore
            "tr")[1].find_all("th")[1:]  # type: ignore

        def parse_court_num(court_name: str) -> int:
            return int(court_name.split(' ')[-1])

        return [parse_court_num(th.text.strip()) for th in ths]


def _parse_time(time_str: str) -> HourSlot:
    time = time_str.split('-')
    return HourSlot(
        from_hour=int(time[0].strip().split(':')[0]),
        to_hour=int(time[1].strip().split(':')[0])
    )
