
from dataclasses import dataclass

import pydantic


@dataclass
class LoginResponse:
    token: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
