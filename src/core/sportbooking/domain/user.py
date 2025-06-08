from dataclasses import dataclass

type UserId = int


@dataclass
class User:
    id: UserId
    name: str
    username: str
    password: str
