import datetime
import pydantic

from misho_api.hour_slot import HourSlotApi
from misho_api.time_slot import TimeSlotApi


class ReserveId(pydantic.BaseModel):
    id: str

    @classmethod
    def from_time_slot(cls, time_slot: TimeSlotApi) -> 'ReserveId':
        """
        Create a ReserveId from a time slot string.
        The time slot should be in the format 'YYYY-MM-DD HH:MM'.
        """
        date = time_slot.date.strftime("%Y%m%d")
        hour_from = f"{time_slot.hour_slot.from_hour:02d}"
        hour_to = f"{time_slot.hour_slot.to_hour:02d}"

        combined = date + hour_from + hour_to

        id = encode(int(combined))
        return cls(id=id)

    def to_time_slot(self) -> TimeSlotApi:
        decoded = str(decode(self.id))
        date = decoded[:8]
        hour_from = decoded[8:10]
        hour_to = decoded[10:12]

        date_parsed = datetime.datetime.strptime(date, "%Y%m%d").date()
        from_parsed = int(hour_from)
        to_parsed = int(hour_to)

        return TimeSlotApi(
            date=date_parsed,
            hour_slot=HourSlotApi(
                from_hour=from_parsed, to_hour=to_parsed
            )
        )


BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(num, alphabet=BASE62):
    """Encode a positive number into Base X and return the string.

    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    if num == 0:
        return alphabet[0]
    arr = []
    arr_append = arr.append  # Extract bound-method for faster access.
    _divmod = divmod  # Access to locals is faster.
    base = len(alphabet)
    while num:
        num, rem = _divmod(num, base)
        arr_append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def decode(string, alphabet=BASE62):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for decoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num
