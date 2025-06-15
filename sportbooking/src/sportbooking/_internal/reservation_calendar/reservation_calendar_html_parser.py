from bs4 import BeautifulSoup, Tag
import datetime
from sportbooking.reservation_calendar import CourtId, HourSlot, ReservationSlot, TimeSlot, UserCourtReservation, UserReservationCalendar


def parse(html: str) -> UserReservationCalendar:
    soup = BeautifulSoup(html, 'lxml')
    names_calendar = NamesParser(soup).parse()
    reservations = CourtReservationParser(soup, names_calendar).parse()
    return reservations


type Name = str
type NamesCalendar = dict[ReservationSlot, Name]
type NamePerCourt = dict[CourtId, Name]

type CourtReservations = dict[CourtId, UserCourtReservation]


class CourtReservationParser:
    def __init__(self, soup: BeautifulSoup, names_calendar: NamesCalendar):
        self._soup = soup
        self._names_calendar = names_calendar

    def parse(self) -> UserReservationCalendar:
        buttons = self._soup.find_all("a", class_="button-legenda")

        dates_objects = self._soup.find_all("font", class_="rekreacija-icon")

        def extract_date(text) -> str:
            return text.split(',')[1].strip()

        dates = [datetime.datetime.strptime(extract_date(date.text), "%d.%m.%Y").date()
                 for date in dates_objects]

        day_tables = [button.parent.parent.parent.parent for button in buttons]

        calendar = {}
        for date, day_table in zip(dates, day_tables):
            courts = self._get_courts(day_table)
            day_calendar = self._parse_day_calendar(day_table, date, courts)
            calendar.update(day_calendar)

        return UserReservationCalendar(user_calendar=calendar)

    def _get_courts(self, table: Tag) -> list[CourtId]:
        ths = table.find("thead").find_all("tr")[1].find_all("th")[1:]

        def parse_court_num(court_name: str) -> int:
            return int(court_name.split(' ')[-1])

        return [parse_court_num(th.text.strip()) for th in ths]

    def _parse_day_calendar(self, table: Tag, date: datetime.date, courts: list[int]) -> dict[ReservationSlot, UserCourtReservation]:
        rows = table.find("tbody").find_all("tr")
        reservations = {}
        for row in rows:
            hour_slot, court_reservations = self._parse_hour_slot(
                row, date, courts)

            for court_num, court_reservation in court_reservations.items():
                slot = ReservationSlot(
                    time_slot=TimeSlot(
                        date=date,
                        hour_slot=hour_slot,
                    ),
                    court=court_num
                )
                reservations[slot] = court_reservation

        return reservations

    def _parse_hour_slot(self, row: Tag, date: datetime.date, court_nums: list[int]) -> tuple[HourSlot, CourtReservations]:
        columns = row.find_all("td")

        time = _parse_time(columns[0].text.strip())

        reservations = {}
        for court_num, court_reservation in zip(court_nums, columns[1:]):
            a = court_reservation.find('a')
            href = None
            href = a['href'] if a else None

            link_for_reservation = None
            link_for_cancellation = None
            if href:
                link_for_reservation = href if 'rezervacijaterena' in href else None
                link_for_cancellation = href if 'otkazivanjerezervacije' in href else None

            # print(self._names_calendar)

            reservation_slot = ReservationSlot(
                time_slot=TimeSlot(
                    date=date,
                    hour_slot=time,
                ),
                court=court_num
            )

            reserved_by = self._names_calendar.get(reservation_slot)

            court_reservation = UserCourtReservation(
                reserved_by=reserved_by,
                reserved_by_user=link_for_cancellation is not None,
                link_for_reservation=link_for_reservation,
                link_for_cancellation=link_for_cancellation
            )

            reservations[court_num] = court_reservation

        return (time, reservations)


class NamesParser:
    def __init__(self, soup: BeautifulSoup):
        self._soup = soup

    def parse(self) -> NamesCalendar:
        heads = self._soup.find_all("thead", class_="poimenimavrijemfont")
        tables = [head.parent for head in heads]

        def extract_table_date(table: Tag):
            main_div = table.parent.parent
            title_div = main_div.find("div")
            day = title_div.text.strip()
            return day.split(',')[1].strip()

        dates = [datetime.datetime.strptime(extract_table_date(table), "%d.%m.%Y").date()
                 for table in tables]

        courts = self._get_courts(tables[0])

        calendar = {}
        for date, table in zip(dates, tables):
            day_calendar = self._parse_day_calendar(date, table, courts)
            calendar.update(day_calendar)

        return calendar

    def _parse_day_calendar(self, date: datetime.date, table: Tag, courts: list[int]) -> dict[ReservationSlot, Name]:
        rows = table.find_all("tbody")
        day_calendar = {}
        for row in rows:
            hour_slot, row_names = self._parse_hour_slot(
                row.find('tr'), courts)

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

        names = {}
        for court_num, slot in zip(court_nums, columns[1:]):
            div = slot.find('div')
            if div is not None:
                names[court_num] = div.text.strip()

        return (time, names)

    def _get_courts(self, table: Tag) -> list[int]:
        ths = table.find("thead").find_all("tr")[1].find_all("th")[1:]

        def parse_court_num(court_name: str) -> int:
            return int(court_name.split(' ')[-1])

        return [parse_court_num(th.text.strip()) for th in ths]


def _parse_time(time_str: str) -> HourSlot:
    time = time_str.split('-')
    return HourSlot(
        from_hour=int(time[0].strip().split(':')[0]),
        to_hour=int(time[1].strip().split(':')[0])
    )
