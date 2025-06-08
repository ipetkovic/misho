from dataclasses import dataclass
import datetime

from core.sportbooking.domain.session_token import SessionToken


@dataclass
class UserToken:
    token: SessionToken
    updated_at: datetime.datetime
