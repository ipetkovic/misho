from dataclasses import dataclass

import pydantic


class SessionToken(pydantic.BaseModel):
    value: str
