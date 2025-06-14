import datetime
import typer


WEEKDAYS = {
    "monday": 0,
    "mon": 0,
    "tuesday": 1,
    "tue": 1,
    "wednesday": 2,
    "wed": 2,
    "thursday": 3,
    "thu": 3,
    "friday": 4,
    "fri": 4,
    "saturday": 5,
    "sat": 5,
    "sunday": 6,
    "sun": 6
}

RESOLVED = {
    'today': datetime.date.today(),
    'tomorrow': datetime.date.today() + datetime.timedelta(days=1)
}


def parse_date_or_weekday(value: str) -> datetime.date:
    # Try parse as date DD.MM.YYYY
    try:
        return datetime.datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        pass

    if value.strip().lower() in RESOLVED:
        return RESOLVED[value.strip().lower()]

    # Try parse as weekday
    weekday = value.strip().lower()
    if weekday not in WEEKDAYS:
        raise typer.BadParameter(
            f"Must be a date DD.MM.YYYY or weekday name (e.g. Monday/Today/Tomorrow), got '{value}'"
        )

    today = datetime.date.today()
    target_weekday = WEEKDAYS[weekday]
    days_ahead = target_weekday - today.weekday()
    if days_ahead < 0:  # Target day already passed this week, get next week's
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)
