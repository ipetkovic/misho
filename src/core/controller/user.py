import pydantic


class User(pydantic.BaseModel):
    name: str
    username: str
    email: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
