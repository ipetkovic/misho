import pydantic


class NotificationApi(pydantic.BaseModel):
    username: str
    message: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
