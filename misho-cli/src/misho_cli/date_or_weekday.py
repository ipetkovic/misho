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
{
  "@timestamp": "2025-06-26T07:30:02.284Z",
  "message": "Sending request",
  "logger_name": "de.codept.commons.http.WsClientLive",
  "thread_name": "ZScheduler-Worker-0",
  "level": "INFO",
  "level_value": 20000,
  "application.home": "/opt/docker",
  "context": {
    "payload": "",
    "payloadSize": 0,
    "format": "STORELOGIX",
    "warehouse": {
      "id": "WH_DE_10026",
      "name": "Storelogix"
    },
    "flow": "STOCK_UPDATE",
    "url": "https://kl-rest-test.storelogix.de:40040/REST/inventory/stock",
    "skus": [],
    "queryParams": {
      "Receiver": [
        "RESTSERVER"
      ],
      "Client": [
        "3PL-000"
      ]
    },
    "headers": {
      "Content-Type": [
        "application/xml"
      ],
      "Accept": [
        "application/xml"
      ]
    },
    "method": "GET",
    "requestId": "c581a356-dcca-4085-8698-8c969e8be19b",
    "auth": "StorelogixAuth",
    "additionalTags": {}
  }
}