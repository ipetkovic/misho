import pydantic

type UserId = int


class UserCreate(pydantic.BaseModel):
    name: str
    username: str
    password: str
    email: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)


class User(pydantic.BaseModel):
    id: UserId
    name: str
    username: str
    password: str
    email: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
