

from datetime import datetime
from misho_server.domain.user import User
import pydantic


class UserTelegramData(pydantic.BaseModel):
    user: User | None
    chat_id: int | None
    username: str
    enable_notifications: bool
    created_at: datetime
    updated_at: datetime

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
