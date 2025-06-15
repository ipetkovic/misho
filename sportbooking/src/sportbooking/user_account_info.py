import pydantic


class UserAccountInfo(pydantic.BaseModel):
    name: str

    model_config = pydantic.ConfigDict(extra='ignore', frozen=True)
