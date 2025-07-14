from enum import Enum
from misho_server.domain.user import UserId
import pydantic


class ReservationUpdateEventType(Enum):
    CREATED = "created"
    CANCELLED = "cancelled"


class ReservationUpdateEvent(pydantic.BaseModel):
    user_id: UserId
    event_type: ReservationUpdateEventType
