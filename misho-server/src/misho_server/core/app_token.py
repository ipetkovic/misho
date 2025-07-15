import pydantic


class AppToken(pydantic.BaseModel):
    token: str
