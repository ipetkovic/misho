from dataclasses import dataclass
import datetime

import pydantic

from misho_server.domain.session_token import SessionToken


class UserToken(pydantic.BaseModel):
    token: SessionToken
    updated_at: datetime.datetime
