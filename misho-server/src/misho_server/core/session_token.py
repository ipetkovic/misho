import pydantic


class SessionToken(pydantic.BaseModel):
    value: str
