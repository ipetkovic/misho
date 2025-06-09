from dataclasses import dataclass

import pydantic

type UserId = int


class User(pydantic.BaseModel):
    id: UserId
    name: str
    username: str
    password: str
